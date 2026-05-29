from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from courses.models import Lesson, Enrollment
from .models import LessonProgress
from .serializers import LessonProgressSerializer


class UpdateProgressAPIView(APIView):
    """
    Endpoint untuk mengupdate durasi tontonan (watched_duration).
    Hanya bisa diakses oleh student yang sudah LOGIN dan sudah ENROLLED.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        # 1. Ambil data Lesson
        lesson = get_object_or_404(Lesson, id=lesson_id)
        student = request.user

        # 2. Cek apakah Student terdaftar (Enrolled) di Course milik Lesson ini
        is_enrolled = Enrollment.objects.filter(
            student=student, 
            course=lesson.course, 
            is_active=True
        ).exists()

        if not is_enrolled:
            return Response(
                {"error": "Anda belum terdaftar di kursus ini."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Ambil atau buat record LessonProgress
        progress, created = LessonProgress.objects.get_or_create(
            student=student,
            lesson=lesson
        )

        # 4. Update watched_duration
        watched_duration = request.data.get("watched_duration")
        if watched_duration is not None:
            try:
                new_duration = int(float(watched_duration)) # Support float from JS
                # Hanya update jika durasi baru lebih besar (mencegah progres mundur)
                if new_duration > progress.watched_duration:
                    progress.watched_duration = new_duration
                    progress.save() # Memanggil _check_completion di models.py
            except ValueError:
                return Response({"error": "watched_duration tidak valid"}, status=400)

        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
