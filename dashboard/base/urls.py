from django.urls import path

from . import views

app_name = 'base'
urlpatterns = [
    # Example: path('getsentences/', views.GetSentencesView.as_view(), name='get_sentences'),
    path('', views.IndexView.as_view(), name='index'),
]