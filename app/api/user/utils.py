import csv
from bs4 import BeautifulSoup
from docx import Document
import re
import PyPDF2
import os
from datetime import datetime 


def get_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def clean_text(str):
    cite_pattern = r'【\d+†source】|【\d+:\d+†source】|【\d+:\d+†fuente】|【.*?】'
    return re.sub(cite_pattern, '', str)


def find_in_csv(list):
    csv_file_path = './data/SenTencias.csv'
    json_data = []
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row['providencia'] in list:
                json_data.append(row)

    return json_data


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def create_docx_from_html(html_content, filename):
    text_content = html_to_text(html_content)
    
    doc = Document()
    
    doc.add_paragraph(text_content)
    
    doc.save(filename)

def get_constitution(str):
    pattern = r"Artículo (?P<number>\d+)"  # Named group to capture the number
    matches = re.findall(pattern, str)
    print("Found:", matches)

    return matches

def proccess_code(codigo):
    codigo = re.sub(r"[^A-Za-z0-9]", "-", codigo)  # Replace non-alphanumeric characters with hyphens
    codigo = re.sub(r"de-", "-", codigo)          # Remove 'de-' followed by a hyphen
    codigo = re.sub(r"-+", "-", codigo)           # Replace multiple consecutive hyphens with a single hyphen
    codigo = re.sub(r"-(\d{2})(\d{2})$", r"-\2", codigo)  # Convert 4-digit years to 2-digit if necessary
    return codigo

def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')

def get_sentencia(str, constitution_list):
    str = str.lower()

    pattern = r"(?i)(providencia|jurisprudencia|sentencia)[^a-zA-Z0-9]*([A-Za-z]*-?\d+[a-zA-Z]*[^a-zA-Z0-9]*(?:de[^a-zA-Z0-9]*)?\d{2,4})"

    sentencia = re.findall(pattern, str, re.IGNORECASE)

    sentencia_list = []
    if sentencia:
        for match in sentencia:
            code = proccess_code(match[1])
            sentencia_list.append(code.upper())

    else:
        # constitution_list = [20, 30]
        csv_file_path = './data/SenTencias.csv'
        folder_name = './data/site_output'

        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            recent_data_sorted = sorted(csv_reader, key=lambda x: parse_date(x['fecha sentencia']), reverse=True)
            for entry in constitution_list:
                pattern = fr"artículo\s+{entry}"
                cnt = 0
                for row in recent_data_sorted:
                    file_name = f"{row['providencia']}.txt"
                    file_path = os.path.join(folder_name, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                            content = content.lower()
                            if re.search(pattern, content, re.IGNORECASE):
                                sentencia_list.append(row['providencia'])
                                cnt = cnt + 1
                                if cnt == 3: break
                            
                    except FileNotFoundError:
                        print(f"The file {file_name} was not found in the folder {folder_name}.")
                    except IOError as e:
                        print(f"An error occurred while reading the file: {e}")
    print(sentencia_list)
    return sentencia_list


