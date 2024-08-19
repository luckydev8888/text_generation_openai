let sentencia_table

function editSentencia (order) {
  var rowData = sentencia_table.row(order - 1).data()

  $.ajax({
    url: 'get/sentencia',
    type: 'POST',
    data: {
      id: rowData._id
    },
    success: function (response) {
      $('#add_sentencia_model #_id')[0].innerHTML = response._id
      $('#add_sentencia_model #providencia')[0].value = response.providencia
      $('#add_sentencia_model #tipo')[0].value = response.tipo
      $('#add_sentencia_model #ano')[0].value = response.ano
      $('#add_sentencia_model #fecha_sentencia')[0].value =
        response.fecha_sentencia
      $('#add_sentencia_model #tema')[0].value = response.tema
      $('#add_sentencia_model #magistrado')[0].value = response.magistrado
      $('#add_sentencia_model #fecha_publicada')[0].value =
        response.fecha_publicada
      $('#add_sentencia_model #expediente')[0].value = response.expediente
      $('#add_sentencia_model #url')[0].value = response.url
      $('#add_sentencia_model #texto')[0].value = response.texto
      $('#add_sentencia_model').modal('show')
    },
    error: function (xhr, status, error) {
      showToast('Error: ' + xhr.responseText)
      $('#add_sentencia_model').modal('hide')
    }
  })
}

function deleteSentencia (order) {
  var rowData = sentencia_table.row(order - 1).data()
  $('#delete_sentencia_modal #delete_id')[0].innerHTML = rowData._id
  $('#delete_sentencia_modal').modal('show')
}

$(document).ready(function () {
  sentencia_table = $('#Sentencia_datatable').DataTable({
    serverSide: true,
    paging: true,
    searching: false,
    initComplete: function (settings, json) {
      $('#body_preloader').hide() // Hide the loading message when done
    },
    preDrawCallback: function (settings) {
      $('#body_preloader').show() // Show the loading message before drawing the table
    },
    drawCallback: function (settings) {
      $('#body_preloader').hide() // Hide the loading message after drawing the table
    },
    ajax: {
      url: 'get',
      type: 'POST'
    },
    order: [[3, 'asc']],
    columnDefs: [
      { orderable: false, targets: 0 },
      { orderable: true, targets: 1 },
      { orderable: true, targets: 2 },
      { orderable: true, targets: 3 },
      { orderable: true, targets: 4 },
      { orderable: true, targets: 5 },
      { orderable: true, targets: 6 },
      { orderable: false, targets: 7 }
    ],
    columns: [
      { data: 'order' },
      { data: 'providencia' },
      { data: 'ano' },
      { data: 'fecha_sentencia' },
      { data: 'fecha_publicada' },
      { data: 'expediente' },
      {
        data: 'url',
        render: function (data, type, row) {
          return `<a href='${data}' target="_blank">${data}</a>`
        }
      },
      {
        data: '_id',
        render: function (data, type, row) {
          return `<div>
          <button type="button" class="btn btn-warning" onclick="editSentencia(${row.order})">Edit</button>
          <button type='button' class='btn btn-danger' onclick="deleteSentencia(${row.order})">Delete</button>
          </div>`
        }
      }
    ]
  })

  $('#add_sentencia').on('click', function () {
    $('#add_sentencia_model #_id')[0].innerHTML = ''
    $('#add_sentencia_model #providencia')[0].value = ''
    $('#add_sentencia_model #tipo')[0].value = ''
    $('#add_sentencia_model #ano')[0].value = ''
    $('#add_sentencia_model #fecha_sentencia')[0].value = ''
    $('#add_sentencia_model #tema')[0].value = ''
    $('#add_sentencia_model #magistrado')[0].value = ''
    $('#add_sentencia_model #fecha_publicada')[0].value = ''
    $('#add_sentencia_model #expediente')[0].value = ''
    $('#add_sentencia_model #url')[0].value = ''
    $('#add_sentencia_model #texto')[0].value = ''

    $('#add_sentencia_model').modal('show')
  })

  $('#sentencia_save').on('click', function () {
    const id = $('#add_sentencia_model #_id')[0].innerHTML
    const providencia = $('#add_sentencia_model #providencia')[0].value
    const tipo = $('#add_sentencia_model #tipo')[0].value
    const ano = $('#add_sentencia_model #ano')[0].value
    const fecha_sentencia = $('#add_sentencia_model #fecha_sentencia')[0].value
    const tema = $('#add_sentencia_model #tema')[0].value
    const magistrado = $('#add_sentencia_model #magistrado')[0].value
    const fecha_publicada = $('#add_sentencia_model #fecha_publicada')[0].value
    const expediente = $('#add_sentencia_model #expediente')[0].value
    const url = $('#add_sentencia_model #url')[0].value
    const texto = $('#add_sentencia_model #texto')[0].value
    const page_info = sentencia_table.page.info()

    $.ajax({
      url: 'save',
      type: 'POST',
      data: {
        id,
        providencia,
        tipo,
        ano,
        fecha_sentencia,
        tema,
        magistrado,
        fecha_publicada,
        expediente,
        url,
        texto
      },
      success: function (response) {
        showToast('Saved successfully!')
        $('#add_sentencia_model').modal('hide')
        sentencia_table.page(page_info.page).draw('page')
      },
      error: function (xhr, status, error) {
        showToast('Error: ' + xhr.responseText)
        $('#add_sentencia_model').modal('hide')
      }
    })
  })

  $('#sentencia_delete').on('click', function () {
    const id = $('#delete_sentencia_modal #delete_id')[0].innerHTML
    const page_info = sentencia_table.page.info()

    $.ajax({
      url: 'delete',
      type: 'POST',
      data: {
        id
      },
      success: function (response) {
        showToast('Deleted successfully!')
        $('#delete_sentencia_modal').modal('hide')
        sentencia_table.page(page_info.page).draw('page')
      },
      error: function (xhr, status, error) {
        showToast('Error: ' + xhr.responseText)
        $('#delete_sentencia_modal').modal('hide')
      }
    })
  })

  $('#scrap_url').on('click', function () {
    const url = $('#add_sentencia_model #url')[0].value
    if (url == '') alert('Please input url')
    else {
      $.ajax({
        url: 'scrap',
        type: 'POST',
        data: {
          url
        },
        success: function (response) {
          showToast('Deleted successfully!')
          $('#add_sentencia_model #texto')[0].value = response.texto
        },
        error: function (xhr, status, error) {
          showToast('Error: ' + xhr.responseText)
        }
      })
    }
  })
})
