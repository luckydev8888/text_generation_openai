$(document).ready(function () {
  // Definition
  let is_upload
  let is_stopped
  var res_summer_element = document.getElementById('resultados_summernote')
  // res_summer_element.summernote({
  //     tabsize: 2,
  //     height: 100
  // });

  // Init variation

  function init () {
    is_upload = false
    is_stopped = false
    $('#resultados_save').prop('disabled', true)
    $('.preloader.sub').hide()
    $('#hole_pdf_viewer').attr('src', '')
    $('#summary_text')[0].innerHTML = ''
    $('#judgement_table tbody')[0].innerHTML = ''
    $('#constitucion_content')[0].innerHTML = ''
    $('#resultados_summernote')[0].innerHTML = ''
    $('#pdf_file')[0].value = ''
  }

  // Ajax Function Group

  function ajax_reset () {
    return $.ajax({
      type: 'POST',
      url: '/api/reset',
      beforeSend: function () {
        $('#preloader').show()
      },
      success: function (response) {
        console.log(response)
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error('Error occur:', status, error)
      },
      complete: function () {
        $('#preloader').hide()
      }
    })
  }

  function ajax_uploadfile (form_data) {
    return $.ajax({
      type: 'POST',
      url: '/api/uploadfile',
      data: form_data,
      contentType: false,
      cache: false,
      processData: false,
      beforeSend: function () {
        $('#pdf_viewer_preloader').show()
      },
      success: function (response) {
        console.log(response)
        is_upload = true
        const response_file = response.message
        $('#hole_pdf_viewer').attr(
          'src',
          '/api/pdf/' + response_file['file_path']
        )
      },
      statusCode: {
        401: function () {
          window.location.href = '/login'
        }
      },
      error: function (xhr, status, error) {
        console.error('Error occur:', status, error)
      },
      complete: function () {
        $('#pdf_viewer_preloader').hide()
      }
    })
  }

  function ajax_summary (is_reload) {
    return $.ajax({
      type: 'POST',
      url: '/api/analysis_pdf',
      success: function (response) {
        $('#summary_preloader').hide()
        console.log(response)
        $('#summary_text')[0].innerHTML = marked.parse(response.message)
      },
      error: function (xhr, status, error) {},
      beforeSend: function () {
        $('#summary_preloader').show()
      },
      statusCode: {
        401: function () {
          window.location.href = '/login'
        }
      }
    })
      .done(function (response) {
        if (is_reload) return
        else return ajax_constitucion(false)
      })
      .fail(function (xhr, status, error) {
        if (is_stopped) {
          $('#summary_preloader').hide()
          $('.tutela_stopbtn').text('Stop')
          $('.tutela_stopbtn').prop('disabled', false)
          is_stopped = false
          return
        } else {
          setTimeout(() => {
            return ajax_summary()
          }, 10000)
        }
      })
  }

  function ajax_judgement (is_reload) {
    return $.ajax({
      type: 'POST',
      url: '/api/analysis_judgement',
      success: function (response) {
        $('#judgement_preloader').hide()
        console.log(response)
        list = response.message
        var txt = ''
        for (i = 0; i < list.length; i++) {
          txt += '<tr>'
          txt += '<td>' + list[i].providencia + '</td>'
          txt += '<td>' + list[i].tipo + '</td>'
          txt += '<td>' + list[i].ano + '</td>'
          txt += '<td>' + list[i]['fecha sentencia'] + '</td>'
          txt += '<td>' + list[i].tema + '</td>'
          txt += '<td>' + list[i].magistrado + '</td>'
          txt += '<td>' + list[i]['fecha publicada'] + '</td>'
          txt += '<td>' + list[i].expediente + '</td>'
          txt +=
            '<td><a href="' + list[i].url + '">' + list[i].url + '</a></td>'
          txt += '</tr>'
        }
        $('#judgement_table tbody')[0].innerHTML = txt
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error('Error occur:', status, error)
      },
      beforeSend: function () {
        $('#judgement_preloader').show()
      },
      statusCode: {
        401: function () {
          window.location.href = '/login'
        }
      }
    })
      .done(function (response) {
        if (is_reload) return
        return ajax_resultados()
      })
      .fail(function () {
        if (is_stopped) {
          $('#judgement_preloader').hide()
          $('.tutela_stopbtn').text('Stop')
          $('.tutela_stopbtn').prop('disabled', false)
          is_stopped = false
          return
        } else {
          setTimeout(() => {
            return ajax_judgement()
          }, 10000)
        }
      })
  }

  function ajax_constitucion (is_reload) {
    return $.ajax({
      type: 'POST',
      url: '/api/analysis_constitucion',
      success: function (response) {
        $('#constitucion_preloader').hide()
        console.log(response)
        $('#constitucion_content')[0].innerHTML = marked.parse(response.message)
      },
      beforeSend: function () {
        $('#constitucion_preloader').show()
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error('Error occur:', status, error)
      },
      statusCode: {
        401: function () {
          window.location.href = '/login'
        }
      }
    })
      .done(function (response) {
        if (is_reload) return
        return ajax_judgement(false)
      })
      .fail(function () {
        if (is_stopped) {
          $('#constitucion_preloader').hide()
          $('.tutela_stopbtn').text('Stop')
          $('.tutela_stopbtn').prop('disabled', false)
          is_stopped = false
          return
        } else {
          setTimeout(() => {
            return ajax_constitucion()
          }, 10000)
        }
      })
  }

  function ajax_resultados (is_reload) {
    return $.ajax({
      type: 'POST',
      url: '/api/analysis_resultados',
      success: function (response) {
        $('#resultados_preloader').hide()
        console.log(response)
        $('#resultados_summernote')[0].innerHTML = marked.parse(
          response.message
        )
        $('#resultados_save').prop('disabled', false)
        $('#analysis').prop('disabled', false)
        $('#reset').prop('disabled', false)
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error('Error occur:', status, error)
      },
      beforeSend: function () {
        $('#resultados_preloader').show()
      },
      statusCode: {
        401: function () {
          window.location.href = '/login'
        }
      }
    }).fail(function () {
      if (is_stopped) {
        $('#resultados_preloader').hide()
        $('.tutela_stopbtn').text('Stop')
        $('.tutela_stopbtn').prop('disabled', false)
        is_stopped = false
        return
      } else {
        setTimeout(() => {
          return ajax_resultados()
        }, 10000)
      }
    })
  }

  // Button Group

  $('#reset').on('click', function (event) {
    ajax_reset().done(function () {
      init()
    })
  })

  $('#pdf_file').on('change', function (event) {
    var form_data = new FormData($('#file_upload_form')[0])
    ajax_uploadfile(form_data)
  })

  $('#analysis').on('click', function (event) {
    if (is_upload) {
      $('#analysis').prop('disabled', true)
      $('#reset').prop('disabled', true)
      ajax_summary(false)
    } else {
      alert('Select the PDF file')
    }
  })

  // Stop buttons

  $('.tutela_stopbtn').on('click', function (event) {
    event.preventDefault()

    is_stopped = true
    $(this).text('Stoping')
    $(this).prop('disabled', true)
  })

  // Reload buttons

  $('#summary_reload').on('click', function (event) {
    ajax_summary(true)
  })

  $('#judgement_reload').on('click', function (event) {
    ajax_judgement(true)
  })

  $('#constitucion_reload').on('click', function (event) {
    ajax_constitucion(true)
  })

  $('#resultados_reload').on('click', function (event) {
    ajax_resultados(true)
  })

  // Save button

  $('#resultados_save').on('click', function (event) {
    content = $('#resultados_summernote')[0].innerHTML
    // if(is_upload){
    fetch('/api/save_resultados', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        content: content
      })
    })
      .then(response => {
        if (response.status === 401) {
          window.location.href = '/login'
        } else response.blob()
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'output.docx'
        document.body.appendChild(a)
        a.click()
        a.remove()
      })
      .catch(console.error)
    // }
  })

  init()
})
