$(document).ready(function () {
  $('#login-btn').on('click', function () {
    const email = $('#login-form #email')[0].value
    const pwd = $('#login-form #password')[0].value
    const is_remember = $('#login-form #basic_checkbox_1')[0].value

    $.ajax({
      url: 'login/user',
      type: 'POST',
      data: { email, pwd },
      success: function (response) {
        window.location.href = '/admin/constdf'
      },
      error: function (xhr, status, error) {
        console.log('Error: ' + xhr.responseText)
      }
    })
  })
})
