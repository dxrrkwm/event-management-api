from django.utils import timezone
from rest_framework import serializers

from events.models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "title", "description", "date", "location", "organizer")
        read_only_fields = ("id", "organizer")

    def validate_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("The event date must be in the future.")
        return value


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)
