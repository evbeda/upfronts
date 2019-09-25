from django.contrib.auth.models import AnonymousUser
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from .models import Upfront
from .views import UpfrontFilter
from .views import download_csv
import csv
import io


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


class TestCsv(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_status_code_200(self):
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)
        self.assertEqual(response.status_code, 200)

    def test_download_csv(self):
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)

        self.assertEqual('text/csv', dict(response.items())['Content-Type'])
        self.assertIn('-upfronts.csv', dict(response.items())['Content-Disposition'])

    def test_download_csv_with_info(self):
        expected_upfront_dict = {
            'is_recoup': 'True',
            'status': 'COMMITED/APPROVED',
            'organizer': 'IDO',
            'account_name': 'EDA',
            'email_organizer': 'juan@eventbrite.com',
            'upfront_projection': '77777.0000000000',
            'contract_signed_date': '2019-04-04',
            'maximum_payment_date': '2019-05-30',
            'payment_date': '2019-05-05',
            'recoup_amount': '55555.0000000000',
            'gtf': '7000.0000000000',
            'gts': '100000.0000000000',
        }
        Upfront.objects.create(
            is_recoup=True,
            status='COMMITED/APPROVED',
            organizer='IDO',
            account_name='EDA',
            email_organizer='juan@eventbrite.com',
            upfront_projection=77777,
            contract_signed_date='2019-04-04',
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)
        response_decode = response.content.decode('utf-8')
        csv_list = csv.reader(io.StringIO(response_decode))
        for row in csv_list:
            csv_set = set(row)
        expected_csv_set = set(list(expected_upfront_dict.values()))
        self.assertEqual(csv_set, expected_csv_set)
