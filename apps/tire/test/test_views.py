from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.accounts.models import User
from apps.tire.models import Tire, RepairRequest

class TireViewSetTests(APITestCase):
    fixtures = [
        'accounts/fixtures/users.json',
        'tire/fixtures/tires.json',
    ]

    def setUp(self):
        self.admin_user = User.objects.get(username='admin_user')
        self.miner_user = User.objects.get(username='miner_user')
        self.technical_user = User.objects.get(username='technical_user')

    def test_list_tires_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('tire-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_list_tires_miner(self):
        self.client.force_authenticate(user=self.miner_user)
        response = self.client.get(reverse('tire-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see their own tires
        for tire in response.data:
            self.assertEqual(tire['owner'], self.miner_user.id)