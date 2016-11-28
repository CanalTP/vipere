# encoding: utf-8
import json
import sys
import requests
import datetime
import utils
import log
import logging
from clingon import clingon

def compute_luminosity(a_color):
    red = int(a_color[0:2], 16)
    green = int(a_color[2:4], 16)
    blue = int(a_color[4:6], 16)
    return (red * 299 + green * 587 + blue * 114)/1000

def is_valid_color(a_color):
    return len(a_color) == 6 and a_color.isalnum()

@clingon.clize
def check_line_colors(environnement, coverage):
    """Lance la vérification de la présence des couleurs des lignes et du texte associé.
    Dans le cas où les deux couleurs sont présentes, le script vérifie le contraste (accessibilité RGAA).
    """
    log.init_log("", "")
    logger = logging.getLogger("vipere")
    logger.info("On teste le coverage [{}] sur l'environnement [{}] ".format(coverage, environnement))

    params = json.load(open('../params.json'))
    assert (environnement in params['environnements']), "L'environnement demandé n'existe pas"
    navitia_url = params['environnements'][environnement]['url']
    navitia_api_key = params['environnements'][environnement]['key']


    detail_test_result =  []
    detail_test_result.append(["coverage", "env", "test_datetime", "object_id", "object_type", "test_category", "error", "infos", "error_level", "wkt"])

    appel_nav_networks = requests.get(navitia_url + "coverage/{}/networks?count=1000".format(coverage), headers={'Authorization': navitia_api_key})
    if appel_nav_networks.status_code != 200 :
        logger.error (">> l'appel navitia a renvoyé une erreur")
        return
    for a_network in appel_nav_networks.json()['networks'] :
        appel_nav = requests.get(navitia_url + "coverage/{}/networks/{}/lines?count=1000&depth=0".format(coverage, a_network['id']), headers={'Authorization': navitia_api_key})
        if appel_nav.json()['pagination']['total_result'] > 1000 :
            logger.error (">> il y a trop de lignes sur le réseau {}, elles n'ont pas toutes été testées".format(a_network['name']))
        if "lines" in appel_nav.json():
            for a_line in appel_nav.json()['lines']:
                color = a_line['color']
                text_color = a_line['text_color']
                if not color or not text_color:
                    message = "il n'y a pas de couleur ou de couleur de texte pour la ligne {} du réseau {}".format(a_line['name'], a_network['name'])
                    result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "couleurs des lignes", "config manquante", message, "red", utils.geojson_to_wkt(a_line['geojson'])]
                    detail_test_result.append(result)
                elif not is_valid_color(color) or not is_valid_color(text_color):
                    message = "la couleur ou la couleur de texte pour la ligne {} du réseau {} est invalide".format(a_line['name'], a_network['name'])
                    result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "couleurs des lignes", "config erronée", message, "red", utils.geojson_to_wkt(a_line['geojson'])]
                    detail_test_result.append(result)
                else :
                    contrast = abs(compute_luminosity(text_color) - compute_luminosity(color))
                    if contrast == 0 :
                        message = "la couleur et la couleur du texte sont identiques pour la ligne {} du réseau {}".format(a_line['name'], a_network['name'])
                        result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "couleurs des lignes", "code de ligne illisible", message, "red", utils.geojson_to_wkt(a_line['geojson'])]
                        detail_test_result.append(result)
                    elif contrast <= 125 :
                        a_better_color = "blanc"
                        if compute_luminosity(color) >= 128 :
                            a_better_color = "noir"
                        message = "il n'y a pas assez de contraste entre la couleur et la couleur du texte pour la ligne {} du réseau {} : du {} serait moins pire".format(a_line['name'], a_network['name'], a_better_color)
                        result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "couleurs des lignes", "code de ligne peu lisible", message, "orange", utils.geojson_to_wkt(a_line['geojson'])]
                        detail_test_result.append(result)

    utils.write_errors_to_file (environnement, coverage, "check_line_colors", detail_test_result)
    utils.generate_file_summary()
