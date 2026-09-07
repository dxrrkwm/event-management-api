from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from events.models import Event, Registration
from events.permissions import IsOrganizerOrReadOnly
from events.serializers import DetailSerializer, EventSerializer
from events.services import send_registration_email


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "title"]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @extend_schema(
        request=None,
        responses={201: DetailSerializer, 400: DetailSerializer},
    )
    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def register(self, request, pk=None):
        event = self.get_object()
        if event.date <= timezone.now():
            return Response(
                {"detail": "This event has already started."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            _, created = Registration.objects.get_or_create(
                event=event, user=request.user
            )
            if not created:
                return Response(
                    {"detail": "You are already registered."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            transaction.on_commit(
                lambda: send_registration_email(event, request.user.email), robust=True
            )
        return Response(
            {"detail": "Registration confirmed."}, status=status.HTTP_201_CREATED
        )

    @extend_schema(request=None, responses={204: None})
    @register.mapping.delete
    def cancel_registration(self, request, pk=None):
        event = self.get_object()
        Registration.objects.filter(event=event, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
