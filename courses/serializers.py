from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "video_url", "total_duration", "order"]


class CourseSerializer(serializers.ModelSerializer):
    # Menampilkan jumlah materi dalam satu course
    lesson_count = serializers.IntegerField(source="lessons.count", read_only=True)
    teacher_name = serializers.CharField(source="teacher.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "teacher_name",
            "lesson_count",
            "created_at",
        ]
