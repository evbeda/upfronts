from django.conf.urls import url
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    # url(r'^upfronts/', views.UpfrontsTableView.as_view(), name='upfronts'),
    url(r'^', RedirectView.as_view(url='/upfronts/'), name='redirect-url'),
]
