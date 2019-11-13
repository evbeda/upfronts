from django.conf.urls import (
    include,
    url,
)
from django.contrib import admin
from django.contrib.auth.views import (
    LogoutView,
)

from app.views import Login

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', Login.as_view(), name='login'),
    url(r'^accounts/logout/$', LogoutView.as_view(), name='logout'),
    url('', include('social_django.urls', namespace='social')),
    url(r'', include('app.urls')),
]
