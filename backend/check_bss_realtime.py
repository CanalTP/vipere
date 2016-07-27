# encoding: utf-8

import json
import sys
import requests
import datetime
import utils
import log
import logging
from clingon import clingon

@clingon.clize
def test_all_bss_for_realtime_on_stands(environnement, coverage, *insee_filter):
    log.init_log("", "")
    logger = logging.getLogger("vipere")
    logger.info("Test du temps réel de la dispo VLS pour le coverage [{}] et sur l'environnement [{}]".format(coverage, environnement))

    params = json.load(open('../params.json'))
    assert (environnement in params['environnements']), "L'environnement demandé n'existe pas"
    navitia_url = params['environnements'][environnement]['url']
    navitia_api_key = params['environnements'][environnement]['key']

    total_nb_tests = 0
    test_result = {}
    test_result['POI hors périmètre'] = 0
    test_result['POI non paramétré'] = 0
    test_result['POI mal paramétré'] = 0
    test_result['POI paramétré mais ko'] = 0
    test_result['POI ok'] = 0

    detail_test_result =  []
    detail_test_result.append(["coverage", "env", "test_datetime", "object_id", "object_type", "test_category", "error", "infos", "error_level", "wkt"])

    appel_nav_url = navitia_url + "coverage/{}/poi_types/poi_type:amenity:bicycle_rental/pois?count=900".format(coverage)
    appel_nav = requests.get(appel_nav_url, headers={'Authorization': navitia_api_key})
    #TODO : gérer la pagination de manière plus fine, sur des gros coverage, on peut avoir plus de POIs

    if appel_nav.status_code != 200 :
        logger.error (">> l'appel navitia a renvoyé une erreur : " + appel_nav_url)
        return

    pois = appel_nav.json()['pois']
    for a_poi in pois :
        if (total_nb_tests % 100) == 0:
            logger.info("Verification du VLS {} sur {}".format(str(total_nb_tests), str(len(pois))))
        total_nb_tests += 1
        if insee_filter != []:
            if a_poi['administrative_regions'][0]['insee'] not in insee_filter :
                test_result['POI hors périmètre'] += 1
                continue

        if len(a_poi['properties']) == 0 :
            result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_poi['id'], "poi", "temps réel VLS", "config manquante", "Pas de propriétés sur ce VLS", "orange", "POINT({} {})".format(a_poi['coord']['lon'],a_poi['coord']['lat'] )  ]
            detail_test_result.append(result)
            test_result['POI non paramétré'] += 1
        else :
            if not "operator" in a_poi['properties'] or not "network" in a_poi['properties'] or not "ref" in a_poi['properties']:
                result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_poi['id'], "poi", "temps réel VLS", "config manquante", "Il manque operator, network ou ref sur ce VLS", "orange", "POINT({} {})".format(a_poi['coord']['lon'],a_poi['coord']['lat'] )  ]
                detail_test_result.append(result)
                test_result['POI mal paramétré'] += 1
                continue
            else :
                if not "stands" in a_poi :
                    result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_poi['id'], "poi", "temps réel VLS", "temps réel ko", "la config a l'air ok, mais ça ne fonctionne pas", "red", "POINT({} {})".format(a_poi['coord']['lon'],a_poi['coord']['lat'] )  ]
                    detail_test_result.append(result)
                    test_result['POI paramétré mais ko'] += 1
                elif a_poi['stands'] is None :
                    result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_poi['id'], "poi", "temps réel VLS", "temps réel ko", "la config a l'air ok, mais le webservice tiers renvoit n'importe quoi", "red", "POINT({} {})".format(a_poi['coord']['lon'],a_poi['coord']['lat'] )  ]
                    detail_test_result.append(result)
                    test_result['POI paramétré mais ko'] += 1
                else :
                    test_result['POI ok'] += 1

    logger.info("Résultat des tests : ")
    logger.info(">> {} cas de tests".format(total_nb_tests))
    logger.info(">> {} VLS pas paramétrés du tout".format(test_result['POI non paramétré']))
    logger.info(">> {} VLS avec des paramètres manquants".format(test_result["POI mal paramétré"]))
    logger.info(">> {} VLS en erreur quoique bien paramétrés".format(test_result['POI paramétré mais ko']))
    logger.info(">> {} VLS ignorés car hors périmètre".format(test_result['POI hors périmètre']))
    logger.info(">> {} VLS qui fonctionnent".format(test_result['POI ok']))

    utils.write_errors_to_file (environnement, coverage, "check_realtime_on_bss", detail_test_result)
    utils.generate_file_summary()
