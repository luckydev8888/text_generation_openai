$(document).ready(function () {
  var const_table = $("#ConstDf_datatable").DataTable({
    serverSide: true,
    paging: true,
    ajax: {
      url: "/admin/constdf/get",
      type: "POST",
    },

    columns: [
      { data: "DT_RowId" },
      { data: "first_name" },
      { data: "last_name" },
      { data: "position" },
      { data: "office" },
    ],
  });

  const_table.on("click", "tbody tr", function () {
    var $row = const_table.row(this).nodes().to$();
    $(".bd-example-modal-lg").modal("show");
  });

  $("#add_const").on("click", function () {
    $("#add_const_model #_id")[0].innerHTML = "";
    $("#add_const_model #art_type")[0].value = "Articulo";
    $("#add_const_model #articulo")[0].value = "";
    $("#add_const_model #texto")[0].value = "";
    $("#add_const_model").modal("show");
  });

  $("#const_save").on("click", function () {
    const id = $("#add_const_model #_id")[0].innerHTML;
    const type = $("#add_const_model #art_type")[0].value;
    const number = $("#add_const_model #articulo")[0].value;
    const texto = $("#add_const_model #texto")[0].value;

    console.log(id, type, number, texto);
    $.ajax({
      url: "admin/const/save",
      type: "POST",
      data: {
        id,
        type,
        number,
        texto,
      },
      success: function (response) {
        console.log("ok");
        showToast("Saved successfully!");
      },
      error: function (xhr, status, error) {
        showToast("Error: " + xhr.responseText);
      },
    });
  });
});
