from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from fcm_django.models import FCMDevice


User = get_user_model()


class DevicesCreateViewTestCase(APITestCase):

    url = "/devices/"

    def create_request(self, data):
        return self.client.post(self.url, data, format="json")

    def login(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )
        self.client.force_authenticate(user=self.user)

    def test_unauthorized_request_returns_401(self):
        response = self.create_request(
            {"registration_id": "test_registration_id", "type": "web"}
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_request_body_returns_400(self):
        self.login()
        response = self.create_request({})
        self.assertEqual(response.status_code, 400)

    def test_valid_request_creates_device(self):
        self.login()
        response = self.create_request(
            {"registration_id": "test_registration_id", "type": "web"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["registration_id"], "test_registration_id")
        self.assertEqual(response.data["type"], "web")

    def test_multiple_requests_with_same_type_creates_multiple_devices(self):
        self.login()
        self.create_request(
            {"registration_id": "test_registration_id_1", "type": "web"}
        )
        self.create_request(
            {"registration_id": "test_registration_id_2", "type": "web"}
        )
        devices = FCMDevice.objects.filter(user=self.user, type="web")
        self.assertEqual(devices[0].active, True)
        self.assertEqual(devices[1].active, True)

    def test_multiple_requests_with_same_registration_id_creates_one_device(self):
        self.login()
        self.create_request({"registration_id": "test_registration_id", "type": "web"})
        self.create_request(
            {"registration_id": "test_registration_id", "type": "android"}
        )
        devices = FCMDevice.objects.filter(user=self.user)
        self.assertEqual(devices.count(), 1)

    def test_device_is_linked_to_user(self):
        self.login()
        self.create_request({"registration_id": "test_registration_id", "type": "web"})
        device = FCMDevice.objects.get(user=self.user)
        self.assertEqual(device.user, self.user)
