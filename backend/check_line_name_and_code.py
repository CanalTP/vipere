# encoding: utf-8

import json
import re
import log
import logging
import requests
import sys
import datetime
import utils
from clingon import clingon

@clingon.clize
def check_lines(environnement, coverage):
    """Lance la vérification de la présence des codes et noms des lignes et qu'ils ne sont pas identiques.
    """
    log.init_log("", "")
    logger = logging.getLogger("vipere")
    logger.info("Vérification des lignes pour le coverage [{}] et sur l'environnement [{}]".format(coverage, environnement))

    params = json.load(open('../params.json'))
    assert (environnement in params['environnements']), "L'environnement demandé n'existe pas"
    navitia_url = params['environnements'][environnement]['url']
    navitia_api_key = params['environnements'][environnement]['key']

    #pour éviter les gros appels, on fait un appel par réseau
    nav_response_network = requests.get(navitia_url + "coverage/{}/networks?count=1000".format(coverage), headers={'Authorization': navitia_api_key})
    if nav_response_network.status_code != 200 :
        logger.error(">> l'appel navitia a renvoyé une erreur")
        return
    errors = []
    errors.append(["coverage", "env", "test_datetime", "object_id", "object_type", "test_category", "error", "infos", "error_level", "wkt"])
    for a_network in nav_response_network.json()['networks'] :
        nav_response_line = requests.get(navitia_url + "coverage/{}/networks/{}/lines/?count=1000".format(coverage, a_network["id"]),
            headers={'Authorization': navitia_api_key})
        if "lines" in nav_response_line.json():
            for a_line in nav_response_line.json()['lines']:
                if a_line["code"].strip() == "":
                    errors.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                        a_line["id"], "line", "check_line_name_and_code", "no_line_code", '"' + a_line["name"].replace('"', '""')+'"', "orange",
                        utils.geojson_to_wkt(a_line['geojson'])])
                if a_line["name"].strip() == "":
                    errors.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                        a_line["id"], "line", "check_line_name_and_code", "no_line_name", a_line["code"], "red",
                        utils.geojson_to_wkt(a_line['geojson'])])
                if a_line["name"].strip() and (a_line["name"].strip() == a_line["code"].strip()):
                    errors.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                        a_line["id"], "line", "check_line_name_and_code", "line_code_and_name_identical", a_line["code"], "orange",
                        utils.geojson_to_wkt(a_line['geojson'])])
        else:
            errors.append([coverage, environnement, datetime.date.today().strftime('%Y%m%d'),
                a_network["id"], "network", "check_line_name_and_code", "network_has_no_line",
                "le réseau {} n'a pas de lignes".format(a_network["name"])
                , "red", ""])
    utils.write_errors_to_file (environnement, coverage, "check_line_name_and_code", errors)
    utils.generate_file_summary()
