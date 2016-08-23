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
def test_network_for_realtime_on_stop_schedule(environnement, coverage, *networks):
    log.init_log("", "")
    logger = logging.getLogger("vipere")
    logger.info("Vérification des lignes pour le coverage [{}] et sur l'environnement [{}]".format(coverage, environnement))

    if len(networks) == 0:
        logger.error("Au moins un identifiant de réseau doit être passé en paramètre")
        exit()
    params = json.load(open('../params.json'))
    assert (environnement in params['environnements']), "L'environnement demandé n'existe pas"
    navitia_url = params['environnements'][environnement]['url']
    navitia_api_key = params['environnements'][environnement]['key']


    total_nb_tests = 0
    test_result = {}
    test_result['ligne non configurée'] = 0
    test_result['pas horaires du tout'] = 0
    test_result["pas horaires mais c'est normal"] = 0
    test_result['horaires théoriques'] = 0
    test_result['OK'] = 0

    detail_test_result =  []
    detail_test_result.append(["coverage", "env", "test_datetime", "object_id", "object_type", "test_category", "error", "infos", "error_level", "wkt"])

    for network in networks:
        appel_nav = requests.get(navitia_url + "coverage/{}/networks/{}/lines?count=0".format(coverage, network), headers={'Authorization': navitia_api_key})
        nb_result = appel_nav.json()['pagination']['total_result']

        appel_nav = requests.get(navitia_url + "coverage/{}/networks/{}/lines?count={}".format(coverage, network, nb_result), headers={'Authorization': navitia_api_key})
        lines = appel_nav.json()['lines']
        for a_line in lines :
            logger.info("Execution du traitement sur le réseau {} et la ligne {}".format(network, a_line["id"]))
            if not "properties" in a_line :
                message = 'pas de configuration temps réel pour la ligne {} ({})'.format(a_line['name'], a_line['id'])
                result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "temps réel mode proxy", "config manquante", message, "green", utils.geojson_to_wkt(a_line['geojson'])  ]
                detail_test_result.append(result)
                test_result['ligne non configurée'] += 1
            else :
                keys = [prop['name'] for prop in a_line['properties']]
                if not "realtime_system" in keys :
                    test_result['ligne non configurée'] += 1
                    message = 'pas de configuration temps réel pour la ligne {} ({})'.format(a_line['name'], a_line['id'])
                    result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d'), a_line['id'], "line", "temps réel mode proxy", "config manquante", message, "green", utils.geojson_to_wkt(a_line['geojson'])  ]
                    detail_test_result.append(result)
                    continue

                #je récupère le nombre de stop_points sur ma ligne
                appel_nav = requests.get(navitia_url + "coverage/{}/networks/{}/lines/{}/stop_points?count=200".format(coverage, network, a_line['id']), headers={'Authorization': navitia_api_key})

                #je fais un appel grille horaire à l'arrêt pour chaque arrêt de la ligne et je vérifie que j'ai du temps réel
                for a_stop_point in appel_nav.json()['stop_points']:
                    appel_nav = requests.get(navitia_url + "coverage/{}/networks/{}/lines/{}/stop_points/{}/stop_schedules?items_per_schedule=1".format(coverage, network, a_line['id'], a_stop_point['id']), headers={'Authorization': navitia_api_key})
                    for a_schedule in appel_nav.json()['stop_schedules'] :
                        wkt = "POINT({} {})".format(a_schedule['stop_point']["coord"]["lon"], a_schedule['stop_point']["coord"]["lat"])
                        total_nb_tests +=1
                        if len(a_schedule['date_times']) == 0 :
                            if a_schedule['additional_informations'] in ["no_departure_this_day", "partial_terminus", "terminus"] :
                                test_result["pas horaires mais c'est normal"] += 1
                                message = "pas d'horaires aujourd'hui pour l'arrêt {}, la ligne {}, le parcours {} ({}, {}, {})".format(a_schedule['stop_point']['name'], a_schedule['route']['line']['code'],  a_schedule['route']['name'], a_schedule['stop_point']['id'], a_schedule['route']['line']['id'],  a_schedule['route']['id'])
                                result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d')
                                    , a_schedule['stop_point']['id'], "stop_point", "temps réel mode proxy", "pas d'horaires aujourd'hui"
                                    , message
                                    , "green", wkt  ]
                                detail_test_result.append(result)
                            else :
                                message = "pas d'horaires pour l'arrêt {}, la ligne {}, le parcours {} ({}, {}, {})".format(a_schedule['stop_point']['name'], a_schedule['route']['line']['code'],  a_schedule['route']['name'], a_schedule['stop_point']['id'], a_schedule['route']['line']['id'],  a_schedule['route']['id'])
                                result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d')
                                    , a_schedule['stop_point']['id'], "stop_point", "temps réel mode proxy", "pas d'horaires"
                                    , message
                                    , "red", wkt  ]
                                detail_test_result.append(result)
                                test_result['pas horaires du tout'] += 1
                        else :
                            if a_schedule['date_times'][0]['data_freshness'] != "realtime":
                                test_result['horaires théoriques'] += 1
                                message = "pas de temps réel pour l'arrêt {}, la ligne {}, le parcours {} ({}, {}, {})".format(a_schedule['stop_point']['name'], a_schedule['route']['line']['code'],  a_schedule['route']['name'], a_schedule['stop_point']['id'], a_schedule['route']['line']['id'],  a_schedule['route']['id'])
                                result = [coverage, environnement, datetime.date.today().strftime('%Y%m%d')
                                    , a_schedule['stop_point']['id'], "stop_point", "temps réel mode proxy", "horaires théoriques"
                                    , message
                                    , "orange", wkt  ]
                                detail_test_result.append(result)
                            else:
                                test_result['OK'] += 1

        logger.info ("Résultat des tests pour le réseau {} : ".format(network))
        logger.info (">> {} cas de tests".format(total_nb_tests))
        logger.info (">> {} ligne(s) sans temps réel configuré".format(test_result['ligne non configurée']))
        logger.info (">> {} cas de services terminés".format(test_result["pas horaires mais c'est normal"]))
        logger.info (">> {} cas où du théorique est renvoyé".format(test_result['horaires théoriques']))
        logger.info (">> {} cas où aucun horaire n'est renvoyé".format(test_result['pas horaires du tout']))
        logger.info (">> {} cas où ça marche !".format(test_result['OK']))

    utils.write_errors_to_file (environnement, coverage, "check_realtime_proxy", detail_test_result)
    utils.generate_file_summary()
