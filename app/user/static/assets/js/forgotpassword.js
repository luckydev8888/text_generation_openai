$(document).ready(function () {
  $("#email_send_button").on("click", function () {
    const email = $("#email")[0].value;
    console.log(email)
    // $.ajax({
    //   url: "login/users",
    //   type: "POST",
    //   data: { email, pwd },
    //   success: function (response) {
    //     window.location.href = "/tutela";
    //   },
    //   error: function (xhr, status, error) {
    //     const response = JSON.parse(xhr.responseText);
    //     showToast(response.message, "danger");
    //     console.log("Error: " + response);
    //   },
    // });
  });
});
