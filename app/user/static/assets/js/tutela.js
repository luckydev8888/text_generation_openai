function SetTitle(str) {
  $("#tutela_save_title")[0].value = str;
}

function OpenTutela(title) {
  $.ajax({
    url: "/api/set/state",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ title: title }),
    success: function (list) {
      location.reload();
    },
    error: function (xhr) {
      var error_response = JSON.parse(xhr.responseText);
      showToast(error_response.message);
    },
  });
}

$(document).ready(function () {
  // Definition
  let is_upload;
  let is_stopped;
  var res_summer_element = document.getElementById("resultados_summernote");

  // Init variation

  function init() {
    return $.ajax({
      type: "POST",
      url: "/api/get/state",
      success: function (data) {
        console.log("page init => ", data);
        $("#tutela #title")[0].innerHTML = data?.title || "No title";
        $("#hole_pdf_viewer").attr(
          "src",
          data.file_name ? "/api/pdf/" + data.file_name : ""
        );
        $("#summary_text")[0].innerHTML = marked.parse(data?.pdf_resume || "");
        $("#summary_preloader").hide();
        $("#constitucion_content")[0].innerHTML = marked.parse(
          data?.constitution || ""
        );

        list = data?.sentence_result || [];
        var txt = "";
        for (i = 0; i < list.length; i++) {
          txt += "<tr>";
          txt += "<td>" + list[i].providencia + "</td>";
          txt += "<td>" + list[i].tipo + "</td>";
          txt += "<td>" + list[i].ano + "</td>";
          txt += "<td>" + list[i]["fecha_sentencia"] + "</td>";
          txt += "<td>" + list[i].tema + "</td>";
          txt += "<td>" + list[i].magistrado + "</td>";
          txt += "<td>" + list[i]["fecha_publicada"] + "</td>";
          txt += "<td>" + list[i].expediente + "</td>";
          txt +=
            '<td><a href="' + list[i].url + '">' + list[i].url + "</a></td>";
          txt += "</tr>";
        }
        $("#judgement_table tbody")[0].innerHTML = txt;

        const evidenceKeys = data?.evidence_checklist || [];
        const evidenceListContainer = $("#evidence_list");
        evidenceListContainer.empty();
        console.log("evidenceKeys => ", evidenceKeys);
        var evidenceHtmlText = "";
        evidenceKeys.forEach((key, index) => {
          var evidenceItemText = `<div class="row mt-4"><h4>${index + 1}. ${
            key["descripcion"]
          }</h4>`;
          const evidence = key["evidencias"];
          evidence.forEach((key1, index1) => {
            evidenceItemText =
              evidenceItemText +
              `<div class="form-check"><input class="form-check-input" type="checkbox" value="${key1["descripcion"]}" id="evidence_${index}_${index1}" />
              <label class="form-check-label" for="evidence_${index}_${index1}">
                ${key1["descripcion"]}
              </label>
            </div>`;
          });
          evidenceItemText = evidenceItemText + "</div>";
          evidenceHtmlText = evidenceHtmlText + evidenceItemText;
        });
        evidenceListContainer[0].innerHTML = evidenceHtmlText;

        $("#submit_evidence").prop("disabled", evidenceHtmlText == "");

        $("#resultados_summernote")[0].innerHTML = marked.parse(
          data?.resultados || ""
        );

        // $("#summary_text")[0].innerHTML = marked.parse(response.message);
        $("#resultados_save").prop(
          "disabled",
          $("#resultados_summernote")[0].innerHTML == ""
        );
        $(".preloader.sub").hide();

        $("#pdf_file")[0].value = "";
        stopBtnRevert();
      },
      error: function (xhr, status, error) {},
      beforeSend: function () {
        $("#summary_preloader").show();
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    });

    is_upload = false;
    is_stopped = false;
  }

  function stopBtnRevert() {
    $(".tutela_stopbtn").text("Stop");
    $(".tutela_stopbtn").prop("disabled", false);
    is_stopped = false;
  }
  // Ajax Function Group

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
        console.log("pdf file uploaded => ", response);
        is_upload = true;
        const response_file = response.message;
        $("#hole_pdf_viewer").attr(
          "src",
          "/api/pdf/" + response_file["file_path"]
        );
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
      error: function (xhr, status, error) {
        console.error("Error occur:", status, error);
      },
      complete: function () {
        $("#pdf_viewer_preloader").hide();
      },
    });
  }

  function ajax_summary(is_reload) {
    console.log("analyse button clicked ... ");
    return $.ajax({
      type: "POST",
      url: "/api/analysis_pdf",
      success: function (response) {
        $("#summary_preloader").hide();
        console.log("openAI response of pdf contents => ", response);
        $("#summary_text")[0].innerHTML = marked.parse(response.message);

        stopBtnRevert();
      },
      error: function (xhr, status, error) {},
      beforeSend: function () {
        $("#summary_preloader").show();
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    })
      .done(function (response) {
        if (is_reload) return;
        else return ajax_constitucion(false);
      })
      .fail(function (xhr, status, error) {
        if (is_stopped) {
          $("#summary_preloader").hide();

          stopBtnRevert();
          return;
        } else {
          setTimeout(() => {
            return ajax_summary(false);
          }, 10000);
        }
      });
  }

  function ajax_judgement(is_reload) {
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
          txt += "<td>" + list[i]["fecha_sentencia"] + "</td>";
          txt += "<td>" + list[i].tema + "</td>";
          txt += "<td>" + list[i].magistrado + "</td>";
          txt += "<td>" + list[i]["fecha_publicada"] + "</td>";
          txt += "<td>" + list[i].expediente + "</td>";
          txt +=
            '<td><a href="' + list[i].url + '">' + list[i].url + "</a></td>";
          txt += "</tr>";
        }
        $("#judgement_table tbody")[0].innerHTML = txt;

        stopBtnRevert();
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#judgement_preloader").show();
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    })
      .done(function (response) {
        if (is_reload) return;
        return ajax_evidence(false);
      })
      .fail(function () {
        if (is_stopped) {
          $("#judgement_preloader").hide();

          stopBtnRevert();
          return;
        } else {
          setTimeout(() => {
            return ajax_judgement(false);
          }, 10000);
        }
      });
  }

  function ajax_constitucion(is_reload) {
    console.log("on going analysis constitution ...");
    return $.ajax({
      type: "POST",
      url: "/api/analysis_constitucion",
      success: function (response) {
        $("#constitucion_preloader").hide();
        console.log(response);
        $("#constitucion_content")[0].innerHTML = marked.parse(
          response.message
        );

        stopBtnRevert();
      },
      beforeSend: function () {
        $("#constitucion_preloader").show();
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    })
      .done(function (response) {
        if (is_reload) return;
        return ajax_judgement(false);
      })
      .fail(function () {
        if (is_stopped) {
          $("#constitucion_preloader").hide();

          stopBtnRevert();
          return;
        } else {
          setTimeout(() => {
            return ajax_constitucion(false);
          }, 10000);
        }
      });
  }

  function ajax_evidence(is_reload) {
    return $.ajax({
      type: "POST",
      url: "/api/analysis_evidence",
      success: function (response) {
        $("#evidence_preloader").hide();
        const evidenceListContainer = $("#evidence_list");
        evidenceListContainer.empty();
        const evidenceKeys = response.message;
        console.log("evidence keys => ", evidenceKeys);
        var evidenceHtmlText = "";
        evidenceKeys.forEach((key, index) => {
          var evidenceItemText = `<div><h4>${index + 1}. ${
            key["descripcion"]
          }</h4>`;
          const evidence = key["evidencias"];
          evidence.forEach((key1, index1) => {
            evidenceItemText =
              evidenceItemText +
              `<div class="form-check"><input class="form-check-input" type="checkbox" value="${key1["descripcion"]}" id="evidence_${index}_${index1}" />
              <label class="form-check-label" for="evidence_${index}_${index1}">
                ${key1["descripcion"]}
              </label>
            </div>`;
          });
          evidenceItemText = evidenceItemText + "</div>";
          evidenceHtmlText = evidenceHtmlText + evidenceItemText;
        });
        evidenceListContainer[0].innerHTML = evidenceHtmlText;
        $("#submit_evidence").prop("disabled", false);

        stopBtnRevert();
      },
      beforeSend: function () {
        $("#evidence_preloader").show();
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    })
      .done(function (response) {
        return;
      })
      .fail(function () {
        if (is_stopped) {
          $("#evidence_preloader").hide();

          stopBtnRevert();
          return;
        } else {
          setTimeout(() => {
            return ajax_evidence(false);
          }, 10000);
        }
      });
  }

  function ajax_resultados(is_reload) {
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

        stopBtnRevert();
      },
      error: function (xhr, status, error) {
        // Handle errors
        console.error("Error occur:", status, error);
      },
      beforeSend: function () {
        $("#resultados_preloader").show();
      },
      statusCode: {
        401: function () {
          window.location.href = "/login";
        },
      },
    }).fail(function () {
      if (is_stopped) {
        $("#resultados_preloader").hide();

        stopBtnRevert();
        return;
      } else {
        setTimeout(() => {
          return ajax_resultados();
        }, 10000);
      }
    });
  }

  // Button Group

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
      ajax_summary(false);
    } else {
      alert("Select the PDF file");
    }
  });

  // Summit evidence

  $("#submit_evidence").on("click", function () {
    var evidence_data = [];
    $("#evidence_list input").each(function () {
      evidence_data.push({
        value: $(this).val(),
        state: $(this).is(":checked"),
      });
    });
    $.ajax({
      url: "/api/submit_evidence",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ evidence_data: evidence_data }),
      success: function (response) {
        showToast(response.message, "success");
        ajax_resultados(false);
      },
      error: function (xhr) {
        var error_response = JSON.parse(xhr.responseText);

        $("#resultados_summernote")[0].innerHTML =
          "<h3>" +
          error_response.message +
          ".</h3><h4 class='mt-3'>Missing evidences:</h4> " +
          error_response.missing_evidences.join("<br>");
      },
    });
  });

  // Stop buttons

  $(".tutela_stopbtn").on("click", function (event) {
    event.preventDefault();

    is_stopped = true;
    $(this).text("Stoping");
    $(this).prop("disabled", true);
  });

  // Reload buttons

  $("#summary_reload").on("click", function (event) {
    ajax_summary(true);
  });

  $("#judgement_reload").on("click", function (event) {
    ajax_judgement(true);
  });

  $("#constitucion_reload").on("click", function (event) {
    ajax_constitucion(true);
  });

  $("#evidence_reload").on("click", function (event) {
    ajax_evidence(true);
  });

  $("#resultados_reload").on("click", function (event) {
    $("#submit_evidence").click();
  });

  // Save button

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
      .then((response) => {
        if (response.status === 401) {
          window.location.href = "/login";
        } else return response.blob();
      })
      .then((blob) => {
        const title = $("#tutela #title")[0].innerHTML;
        const filename = title == "No title" ? "output.docx" : title + ".docx";
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch(console.error);
  });

  const tutelaModalElement = document.getElementById("tutela_save_modal");
  const tutelaSaveModal = new bootstrap.Modal(tutelaModalElement, {
    keyboard: false,
  });
  $("#save_state").on("click", function (event) {
    $("#tutela_save_title")[0].value =
      $("#tutela #title")[0].innerHTML == "No title"
        ? ""
        : $("#tutela #title")[0].innerHTML;
    $.ajax({
      url: "/api/get/list",
      method: "POST",
      success: function (list) {
        const tutela_title_list = $("#tutela_title_list")[0];
        var txt = "";
        for (i = 0; i < list.length; i++) {
          txt += `<button type="button" class="list-group-item list-group-item-action" onclick="SetTitle('${list[i]}')">
            ${list[i]}
          </button>`;
        }
        tutela_title_list.innerHTML = txt;
        tutelaSaveModal.show();
      },
      error: function (xhr) {
        var error_response = JSON.parse(xhr.responseText);
        showToast(error_response.message);
      },
    });
  });

  $("#tutela_confirm_save").on("click", function (event) {
    var title = $("#tutela_save_title")[0].value;
    if (title == "") showToast("Please input the title", "warning");
    else {
      $.ajax({
        url: "/api/save/state",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ title: title }),
        success: function (response) {
          showToast("Saved successfully", "success");
          tutelaSaveModal.hide();
          init();
        },
        error: function (xhr) {
          var error_response = JSON.parse(xhr.responseText);
          showToast(error_response.message, "danger");
        },
      });
    }
  });

  const tutelaLoadModalElement = document.getElementById("tutela_Load_modal");
  const tutelaLoadModal = new bootstrap.Modal(tutelaLoadModalElement, {
    keyboard: false,
  });
  $("#open_state").on("click", function (event) {
    $.ajax({
      url: "/api/get/list",
      method: "POST",
      success: function (list) {
        const tutela_title_list = $("#open_tutela_title_list")[0];
        var txt = "";
        for (i = 0; i < list.length; i++) {
          txt += `<button type="button" class="list-group-item list-group-item-action" onclick="OpenTutela('${list[i]}')">
            ${list[i]}
          </button>`;
        }
        tutela_title_list.innerHTML = txt;
        tutelaLoadModal.show();
      },
      error: function (xhr) {
        var error_response = JSON.parse(xhr.responseText);
        showToast(error_response.message);
      },
    });
  });

  $(".modal-close-btn").on("click", function (event) {
    tutelaLoadModal.hide();
    tutelaSaveModal.hide();
  });

  init();
});
