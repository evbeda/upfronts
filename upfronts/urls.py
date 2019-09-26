from django.conf.urls import (
    include,
    url,
)
from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)

from app import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', LoginView.as_view(template_name='registration/login.html'), name='login'),
    url(r'^accounts/logout/$', LogoutView.as_view(), name='logout'),
    url(r'download', views.download_csv, name='download_csv'),
    url('', include('social_django.urls', namespace='social')),
    url(r'', include('app.urls')),
]
