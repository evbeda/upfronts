from django.test import Client, TestCase
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
from django.urls import reverse
# Create your tests here.
class RedirectTest(TestCase):

    def test_redirect_to_login_when_login_is_required(self):
        c = Client()
        response = c.get("/upfronts/")
        self.assertIn(reverse('login'), response.url)
