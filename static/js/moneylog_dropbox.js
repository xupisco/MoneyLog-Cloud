function initDropbox(reloading) {
    reloading = reloading || false
    $("#report").html('<p style=\'text-align: left;\'> ' + i18n.msgLoading.replace('%s', '&lt;Dropbox home&gt;/Apps/MoneyLog Cloud/txt/' + getSelectedFile())   + '</p>');
    $("#about-dropbox-version").html('<a href=http://github.com/xupisco/MoneyLog-Cloud/commit/' + commit_id + '>' + commit_id.slice(0, 6) + '</a>');

    $("#charts").hide();

    // Add logout link...
    $('#toolbar-controls-wrapper').append('<div id="logout" style="margin-left: 17px; position: relative; height: 30px;"><a href="/logout">Logout</a></div>');
    
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
    return false;  // cancel link action
}

function loadSelectedFile() {
    initDropbox(true);
}
