from django.conf import settings
from django.core.mail import send_mail

from events.models import Event


def send_registration_email(event: Event, email: str) -> None:
    send_mail(
        subject="Event registration confirmed",
        message=(
            f"You registered for {event.title}.\n"
            f"Date: {event.date:%Y-%m-%d %H:%M %Z}\n"
            f"Location: {event.location}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
