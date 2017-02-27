# encoding: utf-8

import os
import sys
import utils
import json
import re
import log
import logging
import requests
import datetime
from clingon import clingon

detail_test_result =  []
ref_nom_propres = []
ref_cities = []

def is_cityname_in_stopname(stop_name, city_name):
    stop_name = stop_name.lower().strip()
    city_name = city_name.lower().replace("-", " ")
    return (city_name != "") and (city_name in stop_name)

def stop_naming_status(stop_name, city_name):
    stop_name = stop_name.replace("'", ' ')
    stop_name = stop_name.replace("-", ' ')
    stop_name = stop_name.replace(".", '')
    stop_name = stop_name.strip()
    # est-ce que l'arret a bien un libellé
    if len(stop_name) == 0:
        return "no_name"
    # est-ce que l'arrêt commence bien par une majuscule
    if (re.match(r"^[A-Z0-9É]", stop_name)) is None:
        return "first_letter_not_upper"
    # est-ce que le nom de la commune est inclus dans le nom de l'arrêt
    if is_cityname_in_stopname(stop_name, city_name):
        return "city_in_name"

    #ensuite, on vérifie mot à mot avec separateur espace
    word_position = 0
    for word in stop_name.split():
        #1 - on passe les séparateurs
        if word in ["/", "\\"]:
            continue
        #2 - on retire les parenthèse s'il y en a
        if word[:1] == "(" and word[-1:] == ")":
            word = word[1:-1]

        #3- On vérifie la casse
        #si le mot est dans la liste des noms propres (avec la casse), il est bien écrit
        if word in ref_nom_propres:
            continue
        word_position += 1
        if word_position == 1:  # 1er mot : 1ere lettre en majuscule (hors nom propres déjà traités)
            #if not word == word.capitalize():
            m = re.match(r"^[A-Z0-9]([a-z0-9àéèêâîôïäö]*)", word)
            if m and ((m.group()) != word):
                return "first_word_problem"  # le mot n'est pas bien écrit
        else:
            #mot normal, il doit être en minuscule
            #                if not word==word.lower():on ajoute une tolérence sur la majuscule
            m = re.match(r"^[A-Z0-9]([a-z0-9àéèêâîôïäö]*)", word)
            if m and (m.group() != word):
                return "other_word_problem"

        #4- on verifie les mots interdits
        if word.lower() in ["aller", "retour"]:
            return "forbidden_word"

        #5- on verifie les abréviations connues
        if word.lower() in ["st", "ste", "bd", "bld", "cc", "av", "ave", "car"]:
            return "shortenings"
    #si tous les critères passent :
    return ""

def load_naming_ref_files(ref_path):
    INSEE_file_path = os.path.join(os.path.realpath(ref_path), "INSEE.csv")
    nompropre_file_path = os.path.join(os.path.realpath(ref_path), "nompropre.txt")
    f = open(nompropre_file_path, encoding='utf8')
    ref_nom_propres = []
    for row in f.readlines():
        ref_nom_propres.append(row.split(';'))
    f.close()

    f = open(INSEE_file_path, encoding='utf8')
    ref_cities = []
    for row in f.readlines():
        r = row.split(';')
        if r[0] == "insee_com": continue
        r[10] = r[10][1:-1].replace('""', '"')
        ref_cities.append(r)
    f.close()

def check_stops_of_a_line(params, env, coverage, stop_type, line_id):
    nav_url = params["environnements"][env]["url"]
    nav_key = params["environnements"][env]["key"]
    assert(stop_type in ["stop_area", "stop_point"]), "Problème à l'appel de la fonction check_stops_of_a_line"

    nav_response_stops = requests.get(nav_url + "coverage/{}/lines/{}/{}s/?count=1000".format(
        coverage, line_id, stop_type),
        headers={'Authorization': nav_key})
    if nav_response_stops.json()["pagination"]['total_result'] > 1000 :
        detail_test_result.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
            line_id, "line", "check_stop_point_and_stop_area_name", "line_has_too_many_stops",
            "la ligne {} a trop de {}, tout n'a pas été testés".format(line_id, stop_type)
            , "red", ""])
    if (stop_type + "s") in nav_response_stops.json():
        for a_stop in nav_response_stops.json()[stop_type + "s"]:
            wkt= ""
            if ("coord" not in a_stop) or \
                ((float(a_stop["coord"]["lat"]) == 0.0) and (float(a_stop["coord"]["lon"]) == 0.0)) :
                    detail_test_result.append([coverage, env, datetime.date.today().strftime('%Y%m%d'),
                        a_stop["id"], "stop_area", "check_stop_basics", "no_coordinates", a_stop['name'], "red",
                        wkt])
                    #on teste quand même le nom de l'arrêt sans commune
                    sns = stop_naming_status(a_stop["name"], "")
            else:
                wkt = "POINT({} {})".format(a_stop["coord"]["lon"], a_stop["coord"]["lat"])
                for city in a_stop["administrative_regions"]:
                    sns = stop_naming_status(a_stop["name"], city["name"])
                    if sns != "": break;
            if sns != "":
                detail_test_result.append([coverage, env, datetime.date.today().strftime('%Y%m%d'),
                    a_stop["id"], stop_type, "check_stop_basics", sns,
                    a_stop["name"],"orange", wkt])
    else:
        detail_test_result.append([coverage, env, datetime.date.today().strftime('%Y%m%d'),
            line_id, "line", "check_stopbasics", "line_has_no_"+stop_type,
            "la ligne {} n'a pas d'arrêt".format(line_id)
            , "red", ""])

@clingon.clize
def check_stops(environnement, coverage):
    log.init_log("", "")
    logger = logging.getLogger("vipere")
    logger.info("Vérification des arrets pour le coverage [{}] et sur [{}]".format(coverage, environnement))

    params = json.load(open('../params.json'))
    nav_url = params["environnements"][environnement]["url"]
    nav_key = params["environnements"][environnement]["key"]

    detail_test_result.append(["coverage", "env", "test_datetime", "object_id", "object_type", "test_category", "error", "infos", "error_level", "wkt"])

    load_naming_ref_files("../../Data_scripts/data/audit/reference")
    #on fait les appels par réseau et par ligne pour faire des appels plus petits
    nav_response_network = requests.get(nav_url + "coverage/{}/networks?count=1000".format(coverage), headers={'Authorization': nav_key})
    if nav_response_network.status_code != 200 :
        logger.error (">> l'appel navitia a renvoyé une erreur")
        return
    for a_network in nav_response_network.json()['networks'] :
        nav_response_line = requests.get(nav_url + "coverage/{}/networks/{}/lines/?count=1000".format(coverage, a_network["id"]),
            headers={'Authorization': nav_key})
        if "lines" in nav_response_line.json():
            if nav_response_line.json()["pagination"]['total_result'] > 1000 :
                detail_test_result.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                    a_network["id"], "network", "check_stop_point_and_stop_area_name", "network_has_too_many_line",
                    "le réseau {} a trop de lignes, elles n'ont pas toutes été testées".format(a_network["name"])
                    , "red", ""])
            for a_line in nav_response_line.json()["lines"]:
                check_stops_of_a_line(params, environnement, coverage, "stop_area", a_line["id"])
                check_stops_of_a_line(params, environnement, coverage, "stop_point", a_line["id"])
        else:
            detail_test_result.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                a_network["id"], "network", "check_stop_point_and_stop_area_name", "network_has_no_line",
                "le réseau {} n'a pas de lignes".format(a_network["name"])
                , "red", ""])
    utils.write_errors_to_file (environnement, coverage, "check_stop_basics", detail_test_result)
    utils.generate_file_summary()
