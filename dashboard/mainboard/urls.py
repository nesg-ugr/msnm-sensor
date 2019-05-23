from django.urls import path

from . import views

app_name = 'mainboard'
urlpatterns = [
    # Example: path('getsentences/', views.GetSentencesView.as_view(), name='get_sentences'),
    path('', views.MainView.as_view(), name='main'),
    path('monitoring/', views.MonitoringView.as_view(), name='monitoring'),
    path('management/', views.ManagementView.as_view(), name='management'),
    #path('test', views.TestView.as_view(), name='test'),
    #path('testjson', views.TestJsonView.as_view(), name='testjson'),
    path('graph/<slug:sid>', views.GraphView.as_view(), name='graph'),
    path('getconf/<slug:sid>', views.GetConfView.as_view(), name='getconf'),
    path('saveconf/<slug:sid>', views.SaveConfView.as_view(), name='saveconf'),
]