from django.conf.urls import (
    include,
    url,
)
from django.contrib import admin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', LoginView.as_view(template_name='registration/login.html'), name='login'),
    url(r'^accounts/logout/$', LogoutView.as_view(), name='logout'),
    url('', include('social_django.urls', namespace='social')),
    url(r'', include('app.urls')),
]
