
function main_onLoad(){
    // add OpenStreetMap tile layers
    var osm = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    });
    var mono = L.tileLayer('http://www.toolserver.org/tiles/bw-mapnik/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    });

    map = L.map('map', {
        center:[48.837212, 2.413],
        zoom: 8,
        layers: [osm]
    });

    // add control
    var baseMaps = {
         "Normal": osm,
         "Noir et blanc": mono
    };
    var overlayMaps = {};
    L.control.layers(baseMaps, overlayMaps).addTo(map);
    L.control.scale().addTo(map);

    $("#tests-cov-selector").change(showTestList);
    load_csv_list();
}

function load_csv_list() {
    url = window.location.href;
    url = url.split("#")[0];
    url = url.substring(0, url.split("?")[0].length - "main.js".length -2);
    csv_base_url = url + "results/files.json";
    $.getJSON(csv_base_url, processFileList);
}

FileContent.prototype.doAfterLoadData = doAfterLoadCategory;

function processFileList(allText) {
    for (var i in allText["files"]){
        file = allText.files[i];
        pf = file.split("_")[0];
        cov = file.split("_")[1];
        test_categ = file.split(".csv")[0].substring(file.indexOf("_")+1);
        test_categ = test_categ.substring(test_categ.indexOf("_")+1);
        fileObj = new FileContent(pf, cov, test_categ);
        data_file_list.push(fileObj);
        fileObj.loadData(file);
    }
    showTestList();
}

function doAfterLoadCategory(){
    showTestList();
}

function showTestList(){
    for (var i in data_file_list){
        obj = data_file_list[i];
        if ($('#tests-env-selector option[value="'+obj.plateform+'"]').length == 0){
            $("#tests-env-selector").append('<option value="'+obj.plateform+'">'+obj.plateform+'</option>');
        }
        if ($('#tests-cov-selector option[value="'+obj.coverage+'"]').length == 0){
            $("#tests-cov-selector").append('<option value="'+obj.coverage+'">'+obj.coverage+'</option>');
        }
    }
    select = document.getElementById('tests-env-selector');
    plateform = $('#tests-env-selector').val();
    coverage = $('#tests-cov-selector').val();

    //on prépare les catégories à afficher avec le nombre d'objets, puis par type d'erreur
    categories = [];
    map_bounds = false;
    for (var i in data_file_list){
        obj = data_file_list[i];
        if ( (obj.plateform == plateform) && ( (coverage == "" ) || (obj.coverage == coverage)) ) {
            if (!obj.loading){
                nb_red = obj.getErrorLevelCount("red");
                nb_orange = obj.getErrorLevelCount("orange");
                nb_green = obj.getErrorLevelCount("green");
                //on ajoute le nombre à la categorie
                category_found = false;
                for (var j in categories){
                    if (categories[j][0] == obj.category) {
                        categories[j][1] += obj.content.length;
                        categories[j][2] += nb_red;
                        categories[j][3] += nb_orange;
                        categories[j][4] += nb_green;
                        category_found = true;
                        break;
                    }
                }
                if (!category_found) categories.push([obj.category, obj.content.length, nb_red, nb_orange, nb_green]);
                obj.showOnMap();
                tmp_bounds= obj.getMapBounds();
                if (tmp_bounds) {
                    if (map_bounds) map_bounds.extend(tmp_bounds);
                    else map_bounds = tmp_bounds;
                }

            }
        } else {
            obj.clearMap();
        }
    }
    if (map_bounds) map.fitBounds(map_bounds);

    str = "<ul>";
    for (var i in categories){
        str += '<li>' + categories[i][0] + " ("+categories[i][1]+")" +
            '&nbsp;<a href="#" onclick="showRawData(\''+categories[i][0]+'\');">' +
            '<i class="fa fa-file-excel-o" aria-hidden="true"></i></a>' + '<br>';
        str += '<span class="error_level_red">'+categories[i][2]+'</span>';
        str += '<span class="error_level_orange">'+categories[i][3]+'</span>';
        str += '<span class="error_level_green">'+categories[i][4]+'</span>';
        str += '</li>';
    }
    str += "</ul> "
    document.getElementById('tests-container').innerHTML=str;
}

function showRawData(categ){
    env = $("#tests-env-selector").val();
    cov = $("#tests-cov-selector").val();
    dataSet = [];
    for (var i in data_file_list){
        obj = data_file_list[i];
        if ((obj.plateform == env) && (obj.category == categ)) {
            if ((cov == "") || (obj.coverage == cov)){
                for (var j in obj.content){
                    dataSet.push([
                        obj.content[j][0],
                        obj.content[j][1],
                        obj.content[j][2],
                        obj.content[j][3],
                        obj.content[j][5],
                        obj.content[j][6],
                        obj.content[j][7]
                    ]);
                }
            }
        }
    }
    if ( $.fn.dataTable.isDataTable( '#data_table' ) ) {
        $('#data_table').DataTable().destroy();
    }

    $('#data_table').DataTable({
        data:dataSet,
        columns:[
            {title: "Cov"},
            {title: "Env"},
            {title: "Date du test"},
            {title: "Objet"},
            {title: "Test"},
            {title: "Erreur"},
            {title: "Notes"}
        ]
    });

    $('#modaltest').modal();
}

var map;
var popup = L.popup();
var regions;
var placesBounds=false;
var selected = null;
var infowindow = null;
data_file_list = [];
main_onLoad();
