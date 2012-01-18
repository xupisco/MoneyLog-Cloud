var firstRun = true;

function startDropboxInterface() {
    oneFile = true;
    useLocalStorage = false;
    isOnline = true;

    hideUI();
    resetData();
    readFromDropBox();
}

function hideUI() {
    $("#tagsArea").hide();
    $("#charts").hide();
    $("#report").html('<p style=\'font-size: 18px; text-align: left; line-height: 20px;\'><strong>Carregando arquivo do Dropbox...</strong><br />Local: <Dropbox home>/Apps/MoneyLog Box/moneylog_data.txt</p>');
}

function readFromDropBox() {
    $.get('/', { reloading: true }, function(data) {
        $("#editordata").val(data);
        $("#editoropen").css('display', 'inline');
        rawData = data;

        parseData();
        showReport();
        setupUI();
    });
}

function updateDropboxFile() {
    $("#editor").prepend("<div id='saving' style='right: 130px; position: absolute; color: #F44; line-height: 24px;'>Salvando...</div>");
    $.post('/update', { data: $("#editordata").val() }, function(data) {
        $("#saving").hide();
        //readFromDropBox();
        rawData = $("#editordata").val();
        parseData();
        showReport();
        editorOff();
    });
}

function setupUI() {
    $("#editoropen").click(editorOn);
    $("#editorclose").click(editorOff);
    $("#editorsave").click(updateDropboxFile);
    $("#editordata").bind((isOpera) ? 'onkeypress' : 'onkeydown', insertTab);
}