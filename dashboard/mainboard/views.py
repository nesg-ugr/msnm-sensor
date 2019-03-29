import json
import os

import yaml
from django.http import HttpResponseBadRequest, HttpResponse
from django.views import View
from django.views.generic import TemplateView

from mainboard.config import EXAMPLE_ROOT, GRAPH_SIZE, MONITORING_ROOT, SYNC_SECONDS
from mainboard.utils import get_monitoring
import pandas as pd


class MainView(TemplateView):
    template_name = 'mainboard/main.html'

    def get_context_data(self, **kwargs):
        context_data = super(MainView, self).get_context_data(**kwargs)
        context_data['sync_seconds'] = SYNC_SECONDS
        routers = ['borderRouter', 'routerR1', 'routerR2', 'routerR3']
        for router in routers:
            stream = open(os.path.join(EXAMPLE_ROOT, router + '.yaml'), 'r')
            content = yaml.load(stream)
            context_data[router + 'SID'] = content['Sensor']['sid']
            context_data[router + 'serverAddress'] = content['Sensor']['server_address']['ip'] + ':' + \
                                              str(content['Sensor']['server_address']['port'])
            if content['Sensor']['remote_addresses']:
                context_data[router + 'remoteAddresses'] = []
                for k, v in content['Sensor']['remote_addresses'].items():
                    context_data[router + 'remoteAddresses'].append({k: v['ip'] + ':' + str(v['port'])})
        return context_data


class GraphView(View):

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()

        sid = kwargs['sid']
        files_path = os.path.join(EXAMPLE_ROOT, sid, MONITORING_ROOT)
        files = os.listdir(files_path)
        files.sort(reverse=True)
        if GRAPH_SIZE < len(files):
            recent_files = files[0:GRAPH_SIZE]
        else:
            recent_files = files
        df_mon, mon_data = get_monitoring(sid, recent_files)
        df_mon['ts'] = pd.to_datetime(df_mon['ts'], format='%Y%m%d%H%M')
        df_mon['ts'] = df_mon['ts'].astype(str)

        data = {
            'ts': df_mon['ts'].tolist(),
            'Qst': df_mon['Qst'].tolist(),
            'Dst': df_mon['Dst'].tolist(),
            'UCLq': df_mon['UCLq'].tolist(),
            'UCLd': df_mon['UCLd'].tolist(),
            'sid': sid
        }

        return HttpResponse(json.dumps(data), content_type="application/json")