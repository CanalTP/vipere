# encoding: utf-8

import os
import sys
import utils
import subprocess
import log
import logging
import json
from clingon import clingon

@clingon.clize
def launch_tests(environnement):
    log.init_log("", "")
    logger = logging.getLogger("vipere")

    params = json.load(open('../params.json'))
    assert (environnement in params['environnements']), "L'environnement demandé n'existe pas"

    for script in params["tests"]:
        for coverage in params["tests"][script]:
            script_params = ["python3", script+".py", environnement, coverage]
            if type(params["tests"][script]) is dict:
                additional_params = params["tests"][script][coverage]
                logger.debug(str(additional_params))
                if type(additional_params) is str:
                    script_params.append(additional_params)
                else:
                    script_params.extend(additional_params)
            logger.debug("Lancement de : " + str(script_params))
            subprocess.call(script_params)
