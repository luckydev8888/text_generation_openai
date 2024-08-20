$(document).ready(function () {
  let is_upload;
  var res_summer_element = document.getElementById("resultados_summernote");
  // res_summer_element.summernote({
  //     tabsize: 2,
  //     height: 100
  // });

  function init() {
    is_upload = false;
    $("#resultados_save").prop("disabled", true);
    $(".preloader.sub").hide();
    $("#hole_pdf_viewer").attr("src", "");
    $("#summary_text")[0].innerHTML = "";
    $("#judgement_table tbody")[0].innerHTML = "";
    $("#constitucion_content")[0].innerHTML = "";
    $("#resultados_summernote")[0].innerHTML = "";
    $("#pdf_file")[0].value = "";
    $("#resumen").hide();
    $("#sentencias").hide();
    $("#constitucion").hide();
    $("#resultados").hide();
  }

  function ajax_reset() {
    return $.ajax({
      type: "POST",
      url: "/api/reset",
      beforeSend: function () {
        $("#preloader").show();
      },
      success: function (response) {
        console.log(response);
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      complete: function () {
        $("#preloader").hide();
      },
    });
  }

  function ajax_uploadfile(form_data) {
    return $.ajax({
      type: "POST",
      url: "/api/uploadfile",
      data: form_data,
      contentType: false,
      cache: false,
      processData: false,
      beforeSend: function () {
        $("#pdf_viewer_preloader").show();
      },
      success: function (response) {
        console.log(response);
        is_upload = true;
        const response_file = response.message;
        $("#hole_pdf_viewer").attr(
          "src",
          "/api/pdf/" + response_file["file_path"]
        );
      },
      error: function (xhr, status, error) {
        console.error("Error occur:", status, error);
      },
      complete: function () {
        $("#pdf_viewer_preloader").hide();
      },
    });
  }

  function ajax_summary() {
    return $.ajax({
      type: "POST",
      url: "/api/analysis_pdf",
      success: function (response) {
        $("#summary_preloader").hide();
        console.log(response);
        $("#summary_text")[0].innerHTML = marked.parse(response.message);
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#resumen").show();
        $("#summary_preloader").show();
        $("#judgement_preloader").show();
        $("#constitucion_preloader").show();
        $("#resultados_preloader").show();
      },
    })
      .done(function (response) {
        // return ajax_constitucion();
      })
      .fail(function (xhr, status, error) {
        return ajax_summary();
      });
  }

  function ajax_judgement() {
    return $.ajax({
      type: "POST",
      url: "/api/analysis_judgement",
      success: function (response) {
        $("#judgement_preloader").hide();
        console.log(response);
        list = response.message;
        var txt = "";
        for (i = 0; i < list.length; i++) {
          txt += "<tr>";
          txt += "<td>" + list[i].providencia + "</td>";
          txt += "<td>" + list[i].tipo + "</td>";
          txt += "<td>" + list[i].ano + "</td>";
          txt += "<td>" + list[i]["fecha sentencia"] + "</td>";
          txt += "<td>" + list[i].tema + "</td>";
          txt += "<td>" + list[i].magistrado + "</td>";
          txt += "<td>" + list[i]["fecha publicada"] + "</td>";
          txt += "<td>" + list[i].expediente + "</td>";
          txt +=
            '<td><a href="' + list[i].url + '">' + list[i].url + "</a></td>";
          txt += "</tr>";
        }
        $("#judgement_table tbody")[0].innerHTML = txt;
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#sentencias").show();
      },
    })
      .done(function (response) {
        return ajax_resultados();
      })
      .fail(function () {
        return ajax_judgement();
      });
  }

  function ajax_constitucion() {
    return $.ajax({
      type: "POST",
      url: "/api/analysis_constitucion",
      success: function (response) {
        $("#constitucion_preloader").hide();
        console.log(response);
        $("#constitucion_content")[0].innerHTML = marked.parse(
          response.message
        );
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#constitucion").show();
      },
    })
      .done(function (response) {
        return ajax_judgement();
      })
      .fail(function () {
        return ajax_constitucion();
      });
  }

  function ajax_resultados() {
    return $.ajax({
      type: "POST",
      url: "/api/analysis_resultados",
      success: function (response) {
        $("#resultados_preloader").hide();
        console.log(response);
        $("#resultados_summernote")[0].innerHTML = marked.parse(
          response.message
        );
        $("#resultados_save").prop("disabled", false);
        $("#analysis").prop("disabled", false);
        $("#reset").prop("disabled", false);
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#resultados").show();
      },
    }).fail(function () {
      return ajax_resultados();
    });
  }

  $("#reset").on("click", function (event) {
    ajax_reset().done(function () {
      init();
    });
  });

  $("#pdf_file").on("change", function (event) {
    var form_data = new FormData($("#file_upload_form")[0]);
    ajax_uploadfile(form_data);
  });

  $("#analysis").on("click", function (event) {
    if (is_upload) {
      $("#analysis").prop("disabled", true);
      $("#reset").prop("disabled", true);
      ajax_summary();
    } else {
      alert("Select the PDF file");
    }
  });

  $("#resultados_save").on("click", function (event) {
    content = $("#resultados_summernote")[0].innerHTML;
    // if(is_upload){
    fetch("/api/save_resultados", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        content: content,
      }),
    })
      .then((response) => response.blob())
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "output.docx";
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch(console.error);
    // }
  });

  init();
});
