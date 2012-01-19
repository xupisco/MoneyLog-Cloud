function initDropbox() {
    $("#report").html('<p style=\'text-align: left;\'> ' + i18n.msgLoading.replace('%s', '<Dropbox home>/Apps/MoneyLog Cloud/' + getSelectedFile())   + '</p>');
    $("#charts").hide();
    
    $.get('/', { reloading: true, filename: getSelectedFile() }, function(data) {
        $("#editordata").val(data);
        resetData();
        rawData = data;

        parseData();
        showReport();
        showHideEditButton();
    });
}

function editorSave() {
    $("#editor").prepend("<div id='saving' style='right: 130px; position: absolute; color: #F44; line-height: 24px;'>" + i18n.msgSaving + "</div>");
    $.post('/update', { data: $("#editordata").val(), filename: getSelectedFile() }, function(data) {
        $("#saving").hide();
        //readFromDropBox();
        rawData = $("#editordata").val();
        parseData();
        showReport();
        editorOff();
    });
}

function loadSelectedFile() {
    initDropbox();
}

