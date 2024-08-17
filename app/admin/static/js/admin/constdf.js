let const_table

function editConstDf (order) {
  var rowData = const_table.row(order - 1).data()
  $('#add_const_model #_id')[0].innerHTML = rowData._id
  $('#add_const_model #art_type')[0].value = rowData.articulo.includes(
    'Transitorio'
  )
    ? 'Articulo Transitorio'
    : 'Articulo'

  $('#add_const_model #articulo')[0].value = rowData.articulo
    .split(' ')
    .slice(-1)
  $('#add_const_model #tutela_type')[0].value = rowData.tutela
  $('#add_const_model #texto')[0].value = rowData.texto
  $('#add_const_model').modal('show')
}

function deleteConstDf (order) {
  var rowData = const_table.row(order - 1).data()
  $('#delete_const_modal #delete_id')[0].innerHTML = rowData._id
  $('#delete_const_modal').modal('show')
}

$(document).ready(function () {
  const_table = $('#ConstDf_datatable').DataTable({
    serverSide: true,
    paging: true,
    ajax: {
      url: 'get',
      type: 'POST'
    },
    order: [[1, 'desc']],
    columnDefs: [
      { orderable: false, targets: 0 },
      { orderable: true, targets: 1 },
      { orderable: true, targets: 2 },
      { orderable: true, targets: 3 },
      { orderable: false, targets: 4 }
    ],
    columns: [
      { data: 'order' },
      { data: 'articulo' },
      { data: 'texto' },
      { data: 'tutela' },
      {
        data: '_id',
        render: function (data, type, row) {
          return `<div>
          <button type="button" class="btn btn-warning" onclick="editConstDf(${row.order})">Edit</button>
          <button type='button' class='btn btn-danger' onclick="deleteConstDf(${row.order})">Delete</button>
          </div>`
        }
      }
    ]
  })

  $('#add_const').on('click', function () {
    $('#add_const_model #_id')[0].innerHTML = ''
    $('#add_const_model #art_type')[0].value = 'Articulo'
    $('#add_const_model #articulo')[0].value = ''
    $('#add_const_model #tutela_type')[0].value = 'no'
    $('#add_const_model #texto')[0].value = ''
    $('#add_const_model').modal('show')
  })

  $('#const_save').on('click', function () {
    const id = $('#add_const_model #_id')[0].innerHTML
    const type = $('#add_const_model #art_type')[0].value
    const number = $('#add_const_model #articulo')[0].value
    const texto = $('#add_const_model #texto')[0].value
    const tutela = $('#add_const_model #tutela_type')[0].value
    const page_info = const_table.page.info()

    $.ajax({
      url: 'save',
      type: 'POST',
      data: {
        id,
        type,
        number,
        texto,
        tutela
      },
      success: function (response) {
        showToast('Saved successfully!')
        $('.bd-example-modal-lg').modal('hide')
        const_table.page(page_info.page).draw('page')
      },
      error: function (xhr, status, error) {
        showToast('Error: ' + xhr.responseText)
        $('.bd-example-modal-lg').modal('hide')
      }
    })
  })

  $('#const_delete').on('click', function () {
    const id = $('#delete_const_modal #delete_id')[0].innerHTML
    const page_info = const_table.page.info()

    $.ajax({
      url: 'delete',
      type: 'POST',
      data: {
        id
      },
      success: function (response) {
        showToast('Deleted successfully!')
        $('#delete_const_modal').modal('hide')
        const_table.page(page_info.page).draw('page')
      },
      error: function (xhr, status, error) {
        showToast('Error: ' + xhr.responseText)
        $('#delete_const_modal').modal('hide')
      }
    })
  })
})
