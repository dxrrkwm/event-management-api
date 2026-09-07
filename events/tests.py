from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from events.models import Event, Registration

User = get_user_model()


class EventAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner", "owner@example.com", "Strong-pass-483!"
        )
        self.guest = User.objects.create_user(
            "guest", "guest@example.com", "Strong-pass-483!"
        )
        self.event = Event.objects.create(
            title="Django meetup",
            description="Talks and coffee",
            date=timezone.now() + timedelta(days=7),
            location="Kyiv",
            organizer=self.owner,
        )
        self.url = f"/api/events/{self.event.pk}/"

    def test_signup_and_token_login_logout(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Good-pass-728!",
        }
        response = self.client.post("/api/auth/register/", data)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        self.assertTrue(
            User.objects.get(username="newuser").check_password(data["password"])
        )
        response = self.client.post("/api/auth/login/", data)
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 401)

    def test_signup_validation(self):
        for changes in [{"password": "123"}, {"email": "bad"}, {"username": "owner"}]:
            with self.subTest(changes=changes):
                data = {
                    "username": "new",
                    "email": "new@example.com",
                    "password": "Strong-pass-483!",
                }
                self.assertEqual(
                    self.client.post("/api/auth/register/", data | changes).status_code,
                    400,
                )

    def test_invalid_login(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "owner", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 400)

    def test_public_read_and_search(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.get("/api/events/", {"search": "Kyiv"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            self.client.get("/api/events/", {"search": "missing"}).data["count"], 0
        )
        self.assertEqual(self.client.post("/api/events/", {}).status_code, 401)
        self.assertEqual(self.client.post(self.url + "register/").status_code, 401)

    def test_owner_can_create_update_delete(self):
        self.client.force_authenticate(self.owner)
        data = {
            "title": "Conference",
            "description": "Python talks",
            "location": "Lviv",
            "date": (timezone.now() + timedelta(days=10)).isoformat(),
            "organizer": self.guest.pk,
        }
        response = self.client.post("/api/events/", data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["organizer"], self.owner.pk)
        self.assertEqual(self.client.put(self.url, data).status_code, 200)
        self.assertEqual(
            self.client.patch(self.url, {"title": "Updated"}).status_code, 200
        )
        Registration.objects.create(event=self.event, user=self.guest)
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertFalse(Registration.objects.exists())

    def test_other_user_cannot_edit_or_delete(self):
        self.client.force_authenticate(self.guest)
        self.assertEqual(
            self.client.patch(self.url, {"title": "Changed"}).status_code, 403
        )
        self.assertEqual(self.client.delete(self.url).status_code, 403)

    def test_past_event_date_rejected(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            self.url, {"date": (timezone.now() - timedelta(days=1)).isoformat()}
        )
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_and_cancel(self):
        self.client.force_authenticate(self.guest)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url + "register/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.guest.email])
        self.assertIn(self.event.title, mail.outbox[0].body)
        self.assertEqual(self.client.post(self.url + "register/").status_code, 400)
        self.assertEqual(len(mail.outbox), 1)
        Registration.objects.create(event=self.event, user=self.owner)
        self.assertEqual(self.client.delete(self.url + "register/").status_code, 204)
        self.assertFalse(Registration.objects.filter(user=self.guest).exists())
        self.assertTrue(Registration.objects.filter(user=self.owner).exists())

    def test_database_prevents_duplicate_registration(self):
        Registration.objects.create(event=self.event, user=self.guest)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Registration.objects.create(event=self.event, user=self.guest)

    def test_registration_for_past_or_missing_event(self):
        self.client.force_authenticate(self.guest)
        self.event.date = timezone.now() - timedelta(days=1)
        self.event.save()
        self.assertEqual(self.client.post(self.url + "register/").status_code, 400)
        self.assertEqual(
            self.client.post("/api/events/99999/register/").status_code, 404
        )
        self.assertFalse(Registration.objects.exists())

    def test_email_failure_keeps_registration(self):
        self.client.force_authenticate(self.guest)
        with patch(
            "events.services.send_mail", side_effect=OSError("SMTP unavailable")
        ):
            with self.assertLogs(level="ERROR"):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(self.url + "register/")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Registration.objects.filter(user=self.guest).exists())

    def test_ordering(self):
        later = Event.objects.create(
            title="Later",
            description="Talk",
            location="Online",
            organizer=self.owner,
            date=timezone.now() + timedelta(days=30),
        )
        response = self.client.get("/api/events/", {"ordering": "-date"})
        self.assertEqual(response.data["results"][0]["id"], later.pk)

    def test_documentation_available(self):
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
