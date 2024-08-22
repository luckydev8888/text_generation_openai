function showToast(content, type) {
  var delay = 10000;
  var html = `<div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true"><div class="d-flex"><div class="toast-body h6 p-3 m-0">${content}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>`;
  var toastElement = htmlToElement(html);
  var toastContainer = document.querySelector("#toast-container");
  toastContainer.appendChild(toastElement);

  toastElement.classList.toggle("toast-appear");
  var toast = new bootstrap.Toast(toastElement, {
    delay: delay,
    animation: true,
  });
  toast.show();
  setTimeout(() => {
    toastElement.classList.toggle("toast-appear");
    toastElement.classList.toggle("toast-disappear");
  }, delay - 500);
  setTimeout(() => {
    toastElement.remove();
  }, delay + 10000);
}

function htmlToElement(html) {
  var template = document.createElement("template");
  html = html.trim();
  template.innerHTML = html;
  return template.content.firstChild;
}

function userLogout() {
  const url = window.location.href;

  $.ajax({
    method: "POST",
    url: "/logout",
    success: function (response) {
      // Handle success (e.g., redirect to a login page or show a message)
      window.location.href = url;
    },
    error: function (error) {
      // Handle error (e.g., show an error message to the user)
      console.error("Logout failed:", error);
      alert("An error occurred while logging out. Please try again.");
    },
  });
}