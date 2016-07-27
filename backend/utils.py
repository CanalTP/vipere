# encoding: utf-8

import os
import csv
import json
import geojson
from shapely.geometry import shape

def write_errors_to_file(env_name, coverage, test_category, detail_test_result):
    """ crée le fichier csv de sortie contenant les erreurs des tests exécutés """
    file_name = "{}_{}_{}.csv".format(env_name, coverage, test_category )
    out_file = os.path.realpath("../frontend/results/" + file_name)
    with open(out_file, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        for line in detail_test_result:
            writer.writerow(line)

def generate_file_summary():
    """ crée le fichier file.json de sortie listant les fichiers à afficher sur le frontend """
    file_dir = os.path.realpath("../frontend/results/")
    file_list = {"files":[]}
    for f in os.listdir(file_dir):
        full_f = os.path.join(file_dir, f)
        if os.path.isfile(full_f) and (f[-3:]=="csv"):
            file_list["files"].append(f)
    with open(os.path.join(file_dir, "files.json"), mode="w", encoding="utf8") as f:
        json.dump(file_list, f, indent=4, separators=(',', ': '))
        f.close()

def geojson_to_wkt(geojson_data):
    if geojson_data['coordinates'] == []:
        return ""
    g = geojson.loads(json.dumps(geojson_data))
    wkt = shape(g).wkt
    return wkt.replace(", ", ",")

if __name__ == "__main__":
    generate_file_summary()
