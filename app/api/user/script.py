from openai import OpenAI
from .utils import clean_text
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

client = OpenAI(api_key=OPENAI_KEY)

def upload(file_path):

    message_file = client.files.create(
        file=open(file_path, "rb"), purpose="assistants"
    )

    return message_file.id

def openAI_response(send_message, file_id = ""):
    # Create a thread and attach the file to the message

    if file_id == "" : 
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": send_message,
                }
            ]
        )
    else :
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": send_message,
                    # Attach the new file to the message.
                    "attachments": [
                        { "file_id": file_id, "tools": [{"type": "file_search"}] }
                    ],
                }
            ]
        )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=ASSISTANT_ID
    )

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    message_content = messages[0].content[0].text

    output = message_content.value
    output = clean_text(output)

    client.beta.threads.delete(thread.id)

    return output