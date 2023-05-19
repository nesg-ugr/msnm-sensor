import os
import re

import numpy as np
import pandas as pd
import yaml

from mainboard.config import EXAMPLE_ROOT, MONITORING_ROOT, SYNC_SECONDS


def update_context_data_network(context_data):
    context_data['sync_seconds'] = SYNC_SECONDS
    stream = open(os.path.join(EXAMPLE_ROOT, 'global.yaml'), 'r')
    content = yaml.load(stream, Loader=yaml.FullLoader)
    sensors = []
    edges = []
    for k, v in content.items():
        sensors.append({
            'id': k,
            'label': v['label'],
            'ip': v['ip'],
            'port': v['port']
        })
        if v['outputs']:
            for o in v['outputs']:
                edges.append({'from': k, 'to': o})
    context_data['sensors'] = sensors
    context_data['edges'] = edges

    for s in sensors:
        stream = open(os.path.join(EXAMPLE_ROOT, s['id'] + '.yaml'), 'r')
        content_by_id = yaml.load(stream, Loader=yaml.FullLoader)

        # context_data[router + 'SID'] = content['Sensor']['sid']
        # context_data[router + 'serverAddress'] = content['Sensor']['server_address']['ip'] + ':' + \
        #                                   str(content['Sensor']['server_address']['port'])
        if content_by_id['DataSources'].get('remote'):
            s['remoteAddresses'] = []
            for k, v in content_by_id['DataSources']['remote'].items():
                s['remoteAddresses'].append({k: str(content[k]['ip']) + ':' + str(content[k]['port'])})
        if content_by_id['DataSources'].get('local'):
            s['localSources'] = []
            for k, v in content_by_id['DataSources']['local'].items():
                s['localSources'].append(k)
    context_data['sensors'] = sensors
    return context_data


def get_monitoring(sid, files):
    # Contains the ts of each file encountered in the file system
    d_range = []

    # Data matrix from all monitoring files and statistics values involved
    mon_data = np.empty((len(files), 4))

    # Finding missing files
    file_counter = 0
    for i in files:
        ts_file = i[7:][0:-4]
        d_range.append(ts_file)

        # Getting values
        with open(os.path.join(EXAMPLE_ROOT, sid, MONITORING_ROOT, i)) as f:
            control_limits = f.readline()
            q_d_values = f.readline()

        # Getting control limits values
        control_limits = control_limits[1:]  # Removing '#' character
        UCLq = control_limits.split(',')[0].split(':')[1]
        UCLd = control_limits.split(',')[1].split(':')[1]
        UCLd = UCLd.replace('\n', '')

        # Getting Q and D values
        Qst = q_d_values.split(',')[0]
        Dst = q_d_values.split(',')[1]
        Dst = Dst.replace('\n', '')

        # All together
        mon_data[file_counter, :] = np.array([Qst, Dst, UCLq, UCLd])

        file_counter = file_counter + 1

    # Dataframe data
    data = {'ts': d_range, 'files': files}

    # Create dataframe
    df = pd.DataFrame(data)

    # Dataframe containing the
    df_statistics = pd.DataFrame(mon_data, columns=['Qst', 'Dst', 'UCLq', 'UCLd'])

    # Concat both of them
    df_complete = pd.concat([df, df_statistics], axis=1)

    return df_complete, mon_data

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'