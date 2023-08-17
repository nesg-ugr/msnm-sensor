# -*- coding: utf-8 -*-
"""
    :mod:`API module`
    ===========================================================================
    :synopsis: API that allow to receive the configuration params from the dashboard
    :author: Jaime Gallardo Mateo
    :contact: jaimegallardo@correo.ugr.es
    :organization: University of Granada
    :project: VERITAS - MSNM Sensor
    :since: 
"""

from msnm.modules.config.configure import Configure
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/sendConfig")
async def sendConfig(config: Request):
    # Get the data from the request
    config = await config.json()

    # Get the configuration params and load it into a singleton pattern
    sensor_config_params = Configure()
    sensor_config_params.get_config()

    # Set new configuration params into the singleton pattern
    sensor_config_params.get_config()['Sensor']['lv'] = config['Sensor']['lv']
    sensor_config_params.get_config()['Sensor']['prep'] = config['Sensor']['prep']
    sensor_config_params.get_config()['Sensor']['phase'] = config['Sensor']['phase']
    sensor_config_params.get_config()['Sensor']['dynamiCalibration']['B'] = config['Sensor']['dynamiCalibration']['B']
    sensor_config_params.get_config()['Sensor']['dynamiCalibration']['lambda'] = config['Sensor']['dynamiCalibration']['lambda']
    sensor_config_params.get_config()['Sensor']['dynamiCalibration']['enabled'] = config['Sensor']['dynamiCalibration']['enabled']

    return {
        "status": "SUCCESS",
        "message": "Config receive successfully",
        "data": sensor_config_params.get_config()['Sensor'],
    }
