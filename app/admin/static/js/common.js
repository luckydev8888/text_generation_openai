function showToast(message) {
  $("#admin_toast .toast-body")[0].innerHTML = message;
  $(".toast").toast("show");
}
