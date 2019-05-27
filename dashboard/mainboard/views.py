import json
import os

import yaml
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView

from mainboard.config import EXAMPLE_ROOT, GRAPH_SIZE, MONITORING_ROOT, SYNC_SECONDS
from mainboard.utils import get_monitoring, update_context_data_network
import pandas as pd


class MainView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('login')
    template_name = 'mainboard/main.html'

    def get_context_data(self, **kwargs):
        context_data = super(MainView, self).get_context_data(**kwargs)
        context_data = update_context_data_network(context_data)
        return context_data


class MonitoringView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('login')
    template_name = 'mainboard/monitoring.html'

    def get_context_data(self, **kwargs):
        context_data = super(MonitoringView, self).get_context_data(**kwargs)
        context_data = update_context_data_network(context_data)
        return context_data


class ManagementView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('login')
    template_name = 'mainboard/management.html'

    def get_context_data(self, **kwargs):
        context_data = super(ManagementView, self).get_context_data(**kwargs)
        context_data = update_context_data_network(context_data)
        return context_data


class GraphView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

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


class GetConfView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        sid = self.kwargs['sid']
        stream = open(os.path.join(EXAMPLE_ROOT, sid + '.yaml'), 'r')
        conf = yaml.load(stream, Loader=yaml.FullLoader)
        data = conf['Sensor']
        return HttpResponse(json.dumps(data), content_type="application/json")


class SaveConfView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        sid = self.kwargs['sid']
        stream = open(os.path.join(EXAMPLE_ROOT, sid + '.yaml'), 'r')
        conf = yaml.load(stream, Loader=yaml.FullLoader)
        data = conf['Sensor']
        post = self.request.POST
        rename = False
        if not data['sid'] == post['sid']:
            rename = True
        data['sid'] = post['sid']
        data['lv'] = int(post['lv'])
        data['phase'] = int(post['phase'])
        data['prep'] = int(post['prep'])
        data['dynamiCalibration']['B'] = int(post['B'])
        data['dynamiCalibration']['lambda'] = float(post['lambda'])
        data['dynamiCalibration']['enabled'] = bool(int(post['enabled']))
        conf['Sensor'] = data
        output = open(os.path.join(EXAMPLE_ROOT, sid + '.yaml'), 'w+')
        yaml.dump(conf, output, allow_unicode=True, sort_keys=False)
        stream.close()
        output.close()
        if rename:
            os.rename(os.path.join(EXAMPLE_ROOT, sid + '.yaml'), os.path.join(EXAMPLE_ROOT, str(post['sid']) + '.yaml'))
        return HttpResponse(json.dumps({'success': True}), content_type="application/json")


        # $("#sid_field").val(out.sid);
        # $("#lv_field").val(out.lv);
        # $("#phase_field").val(out.phase);
        # $("#prep_field").val(out.prep);
        # $("#lambda_field").val(out.dynamiCalibration.lambda );
        # $("#b_field").val(out.dynamiCalibration.B);
        # $("#enabled_field").val(1);


class TestView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy('login')
    template_name = 'mainboard/test.html'

    def get_context_data(self, **kwargs):
        context_data = super(TestView, self).get_context_data(**kwargs)
        stream = open(os.path.join(EXAMPLE_ROOT, 'global.yaml'), 'r')
        content = yaml.load(stream)
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
        return context_data


class TestJsonView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        data = {
          "nodes": [
            {
              "id": "n0",
              "label": "A node",
              "x": 0,
              "y": 0,
              "size": 3
            },
            {
              "id": "n1",
              "label": "Another node",
              "x": 3,
              "y": 1,
              "size": 2
            },
            {
              "id": "n2",
              "label": "And a last one",
              "x": 1,
              "y": 3,
              "size": 1
            }
          ],
          "edges": [
            {
              "id": "e0",
              "source": "n0",
              "target": "n1"
            },
            {
              "id": "e1",
              "source": "n1",
              "target": "n2"
            },
            {
              "id": "e2",
              "source": "n2",
              "target": "n0"
            }
          ]
        }
        return JsonResponse(data, safe=False)