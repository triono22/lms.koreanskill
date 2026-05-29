from django.conf import settings
from django.db import models


class LessonProgress(models.Model):
    """
    Tracks a student's progress on a specific lesson.

    Logic: If watched_duration >= 80% of the lesson's total_duration,
    the lesson is automatically marked as completed via the save() method.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        verbose_name="Student",
    )
    lesson = models.ForeignKey(
        "courses.Lesson",
        on_delete=models.CASCADE,
        related_name="progress_records",
        verbose_name="Lesson",
    )
    watched_duration = models.PositiveIntegerField(
        default=0,
        verbose_name="Durasi Ditonton (detik)",
        help_text="Berapa detik video yang sudah ditonton oleh student.",
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Selesai",
        help_text="Otomatis True jika watched_duration >= 80% total_duration.",
    )
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Satu student hanya punya satu record progress per lesson
        unique_together = ["student", "lesson"]
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress"

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{self.student.username} - {self.lesson.title} {status}"

    # ------------------------------------------------------------------
    # AUTO-COMPLETE LOGIC
    # Jika watched_duration >= 80% dari total_duration lesson,
    # maka is_completed otomatis di-set menjadi True.
    # ------------------------------------------------------------------
    COMPLETION_THRESHOLD = 0.80  # 80%

    def save(self, *args, **kwargs):
        """Override save to auto-mark completion based on watch progress."""
        self._check_completion()
        super().save(*args, **kwargs)

    def _check_completion(self):
        """
        Cek apakah student sudah menonton >= 80% dari total durasi lesson.
        Jika ya, set is_completed = True secara otomatis.
        """
        total = self.lesson.total_duration
        if total > 0 and self.watched_duration >= (total * self.COMPLETION_THRESHOLD):
            self.is_completed = True

    @property
    def progress_percentage(self):
        """Menghitung persentase progress menonton (0-100)."""
        total = self.lesson.total_duration
        if total <= 0:
            return 0
        pct = (self.watched_duration / total) * 100
        return min(pct, 100)  # Cap at 100%

# ==============================================================================
# REKAP NILAI (PROXY MODEL)
# ==============================================================================
from django.contrib.auth import get_user_model
User = get_user_model()

class StudentGradeRecord(User):
    """
    Virtual model to display student grade summaries inside the Attendance admin section.
    Does not create a new database table.
    """
    class Meta:
        proxy = True
        verbose_name = "Rekap Nilai"
        verbose_name_plural = "Rekap Nilai Siswa"

