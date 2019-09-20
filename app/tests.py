from django.test import Client, TestCase
from django.urls import reverse
from .models import Upfront
from .views import UpfrontFilter


class RedirectTest(TestCase):

    def test_redirect_to_login_when_login_is_required(self):
        c = Client()
        response = c.get("/upfronts/")
        self.assertIn(reverse('login'), response.url)


class FilterTest(TestCase):

    def test_filter_text(self):
        up1 = Upfront.objects.create(
                is_recoup=True,
                status='COMMITED/APPROVED',
                organizer='EDA',
                account_name='AgustinD',
                email_organizer='agustin@eventbrite.com',
                upfront_projection=77777,
                contract_signed_date='2019-04-04',
                maximum_payment_date='2019-05-30',
                payment_date='2019-05-05',
                recoup_amount=55555,
                gtf=100000,
                gts=7000,
        )
        up2 = Upfront.objects.create(
                is_recoup=True,
                status='COMMITED/APPROVED',
                organizer='IDO',
                account_name='EDA',
                email_organizer='JuanPablo@eventbrite.com',
                upfront_projection=77777,
                contract_signed_date='2019-04-04',
                maximum_payment_date='2019-05-30',
                payment_date='2019-05-05',
                recoup_amount=55555,
                gtf=100000,
                gts=7000,
        )
        up3 = Upfront.objects.create(
                is_recoup=True,
                status='COMMITED/APPROVED',
                organizer='Me',
                account_name='Bucolo',
                email_organizer='Walter@eventbrite.com',
                upfront_projection=77777,
                contract_signed_date='2019-04-04',
                maximum_payment_date='2019-05-30',
                payment_date='2019-05-05',
                recoup_amount=55555,
                gtf=100000,
                gts=7000,
        )
        qs = Upfront.objects.all()
        f = UpfrontFilter()
        result = f.search_organizer(qs, '', 'EDA')
        self.assertIn(up1, result)
        self.assertIn(up2, result)
        self.assertNotIn(up3, result)
