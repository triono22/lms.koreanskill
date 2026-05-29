from rest_framework import serializers
from .models import LessonProgress


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ["watched_duration", "is_completed", "progress_percentage", "last_watched_at"]
        read_only_fields = ["is_completed", "progress_percentage", "last_watched_at"]
