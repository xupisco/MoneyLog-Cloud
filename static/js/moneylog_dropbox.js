var commit_id = '89780a3871'

function initDropbox(reloading) {
    reloading = reloading || false
    $("#report").html('<p style=\'text-align: left;\'> ' + i18n.msgLoading.replace('%s', '&lt;Dropbox home&gt;/Apps/MoneyLog Cloud/txt/' + getSelectedFile())   + '</p>');
    $("#app-version").html('commit: <a href="http://github.com/xupisco/MoneyLog-Box" target="_blank">' + commit_id + '</a>');

    $("#charts").hide();
    
    $.get('/', { reloading: reloading, filename: getSelectedFile() }, function(data) {
        $("#editordata").val(data);
        resetData();
        rawData = data;

        parseData();
        showReport();
        showHideEditButton();
    });
}

function editorSave() {
    $("#editor-buttons").prepend("<div id='saving' style='right: 220px; position: absolute; color: #F44; line-height: 50px;'>" + i18n.msgSaving + "</div>");
    $.post('/update', { data: $("#editor-data").val(), filename: getSelectedFile() }, function(data) {
        $("#saving").hide();
        //readFromDropBox();
        rawData = $("#editor-data").val();
        parseData();
        showReport();
        editorOff();
    });
}

function loadSelectedFile() {
    initDropbox(true);
}

