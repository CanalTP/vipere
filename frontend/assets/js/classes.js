class FileContent{
    constructor(plateform, coverage, category) {
        this.plateform = plateform;
        this.category = category;
        this.coverage = coverage;
        this.content = [];
        this.loading = false;
        this.selected = false;
        this.map_markers = L.markerClusterGroup();
    }
}

FileContent.prototype.getErrorLevelCount = function(error_level) {
    nb = 0;
    for (i in this.content){
        if (error_level == this.content[i][8]) nb +=1;
    }
    return nb;
}

FileContent.prototype.loadData = function(csv_file_name) {
    this.loading = true;
    url = window.location.href.split('#')[0];
    url = url.substring(0, url.split("?")[0].length - "main.js".length -2);
    csv_base_url = url + "results/";

    $.ajax({
        type: "GET",
        url: csv_base_url + csv_file_name,
        dataType: "text",
        obj: this,
        success: function(data) {this.obj.processData(data);},
        error: function(data) {console.log("erreur à la lecture du fichier CSV");}
     });
}

FileContent.prototype.doAfterLoadData = function(){};

FileContent.prototype.processData = function(allText) {
    var separator = ";";
    var allTextLines = allText.split(/\r\n|\n/);
    var headers = allTextLines[0].split(separator);
    var lines = [];

    for (var i=1; i<allTextLines.length; i++) {
        var data = allTextLines[i].split(separator);
        if (data.length == headers.length) {

            var tarr = [];
            for (var j=0; j<headers.length; j++) {
                tarr.push(data[j]);
            }
            lines.push(tarr);
        }
    }
    this.content = lines;
    this.loading = false;
    if (this.doAfterLoadData) this.doAfterLoadData();
}


// Returns a Leaflet `LatLngBounds` object.
// see: http://leafletjs.com/reference.html#latlngbounds
var getBounds = function (markersObj) {
    for (Obj in markersObj){
        console.log(markersObj[i]);
        var latLng = markersObj[i].getLatLng();
        console.log(latLng);
        exit();
        if (maxLat) maxLat = max(maxLat, latLng['lat']);
        else maxLat = latLng['lat'];
        if (maxLon) maxLon = max(maxLon, latLng['lon']);
        else maxLon = latLng['lon'];
        if (minLat) minLat = min(minLat, latLng['lat']);
        else minLat = latLng['lat'];
        if (minLon) minLon = min(minLon, latLng['lon']);
        else minLon = latLng['lon'];
    }
  var southWest = new L.LatLng(minLat, minLng);
  var northEast = new L.LatLng(maxLat, maxLng);
  return new L.LatLngBounds(southWest, northEast);
}

FileContent.prototype.getMapBounds = function(){
    try {
        var maxLat = false;
        var minLat = false;
        var maxLon = false;
        var minLon = false;
        for (i in this.content){
            wkt = this.content[i][9];
            if (wkt.length > 0){
                geoJson = wkt2geojson(wkt);
                if (geoJson.type == "Point"){
                    if (maxLat) maxLat = Math.max(maxLat, geoJson.coordinates[1]);
                    else maxLat = geoJson.coordinates[1];
                    if (maxLon) maxLon = Math.max(maxLon, geoJson.coordinates[0]);
                    else maxLon = geoJson.coordinates[0];
                    if (minLat) minLat = Math.min(minLat, geoJson.coordinates[1]);
                    else minLat = geoJson.coordinates[1];
                    if (minLon) minLon = Math.min(minLon, geoJson.coordinates[0]);
                    else minLon = geoJson.coordinates[0];
                }
            }
        }
        if (maxLat && maxLon && minLat && minLon) {
            var southWest = new L.LatLng(minLat, minLon);
            var northEast = new L.LatLng(maxLat, maxLon);
            return new L.LatLngBounds(southWest, northEast);
        } else return false;
    }
    catch(err){
        console.log("getMapBounds - Exception levée sur " + this.plateform + " " + this.category + " " + this.coverage);
    }
}

FileContent.prototype.clearMap = function(){
    this.map_markers.clearLayers();
}

FileContent.prototype.showOnMap = function(){
    try{
        current_id = "";
        this.clearMap();
        for (i in this.content){
            wkt = this.content[i][9];
            if (wkt.length > 0){
                current_id = this.content[i][3];
                geoJson = wkt2geojson(wkt);
                m = L.geoJson(geoJson);
                popupContent = "coverage: " + this.content[i][0] + "<br>";
                popupContent += "Env.: " + this.content[i][1] + "<br>";
                popupContent += "Date test: " + this.content[i][2] + "<br>";
                popupContent += "Object ID: " + this.content[i][3] + "<br>";
                popupContent += "Test: " + this.content[i][5] + "<br>";
                popupContent += "Type Erreur: " + this.content[i][8] + "<br>";
                popupContent += "Erreur: " + this.content[i][6] + "<br>";
                popupContent += "Infos: " + this.content[i][7] + "<br>";
                m.bindPopup(popupContent);
                this.map_markers.addLayer(m);
            }
        }
        map.addLayer(this.map_markers);
    }
    catch(err){
        console.log("showOnMap - Exception levée sur " + this.plateform + " " + this.category + " " + this.coverage + " " + current_id);
    }
}
