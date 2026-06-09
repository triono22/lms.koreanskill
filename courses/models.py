from django.conf import settings
from django.db import models


class Course(models.Model):
    """A course contains multiple lessons."""

    title = models.CharField(max_length=255, verbose_name="Judul")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    cover_image = models.ImageField(
        upload_to="courses/covers/",
        blank=True,
        null=True,
        verbose_name="Gambar Sampul",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_taught",
        verbose_name="Pengajar",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """A single lesson/materi inside a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Course",
    )
    title = models.CharField(max_length=255, verbose_name="Judul Materi")
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL Video (YouTube)",
        help_text="Link video materi (YouTube)",
    )
    video_file = models.FileField(
        upload_to="lessons/videos/",
        blank=True,
        null=True,
        verbose_name="File Video (Upload)",
        help_text="Upload video langsung ke server.",
    )
    total_duration = models.PositiveIntegerField(
        default=0,
        verbose_name="Durasi Total (detik)",
        help_text="Durasi video dalam satuan detik.",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Urutan",
        help_text="Urutan tampil materi dalam course.",
    )
    attachment = models.FileField(
        upload_to="lessons/attachments/",
        blank=True,
        null=True,
        verbose_name="Lampiran Dokumen",
        help_text="File dokumen pendukung (PDF, Docx, dll.)",
    )
    attachment_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Link/URL Dokumen",
        help_text="Tautan eksternal (Google Drive, dll.) untuk dokumen materi.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"

    def __str__(self):
        return f"{self.order}. {self.title}"

    @property
    def get_formatted_duration(self):
        if not self.total_duration:
            return "0m 0s"
        minutes, seconds = divmod(self.total_duration, 60)
        return f"{minutes}m {seconds}s"


class Enrollment(models.Model):
    """Links a student to a course."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Student",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Course",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Status Aktif")

    class Meta:
        unique_together = ["student", "course"]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


# =============================================
# QUIZ SYSTEM
# =============================================

class Quiz(models.Model):
    QUIZ_TYPES = (
        ('quiz', 'Kuis'),
        ('exam', 'Ujian'),
        ('listening', 'Mendengarkan'),
    )
    
    """A quiz belongs to a course."""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="quizzes", verbose_name="Course"
    )
    quiz_type = models.CharField(max_length=10, choices=QUIZ_TYPES, default='quiz', verbose_name="Tipe")
    title = models.CharField(max_length=255, verbose_name="Judul")
    description = models.TextField(blank=True, verbose_name="Deskripsi")
    audio_file = models.FileField(
        upload_to="quizzes/audio/",
        blank=True,
        null=True,
        verbose_name="File Audio (Listening)",
        help_text="Upload audio file untuk soal mendengarkan."
    )
    duration_minutes = models.PositiveIntegerField(
        default=0, 
        verbose_name="Waktu Pengerjaan (Menit)",
        help_text="Isi 0 jika tidak ada batas waktu."
    )
    deadline = models.DateTimeField(blank=True, null=True, verbose_name="Batas Waktu")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class QuizQuestion(models.Model):
    """A single question in a quiz (multiple choice)."""
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="Quiz"
    )
    question_text = models.TextField(verbose_name="Pertanyaan")
    audio_file = models.FileField(
        upload_to="questions/audio/",
        blank=True,
        null=True,
        verbose_name="File Audio (Listening)",
        help_text="Upload audio file untuk soal mendengarkan ini."
    )
    image_file = models.ImageField(
        upload_to="questions/images/",
        blank=True,
        null=True,
        verbose_name="Gambar Soal",
        help_text="Upload file gambar untuk soal ini."
    )
    audio_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL Audio (Listening)",
        help_text="Atau masukkan URL audio langsung (hanya baca, tanpa unduh ke server)."
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL Gambar Soal",
        help_text="Atau masukkan URL gambar langsung (hanya baca, tanpa unduh ke server)."
    )
    option_a = models.CharField(max_length=500, verbose_name="Opsi A")
    option_b = models.CharField(max_length=500, verbose_name="Opsi B")
    option_c = models.CharField(max_length=500, verbose_name="Opsi C")
    option_d = models.CharField(max_length=500, verbose_name="Opsi D")

    ANSWER_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    correct_answer = models.CharField(
        max_length=1, choices=ANSWER_CHOICES, verbose_name="Jawaban Benar"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan")

    class Meta:
        ordering = ["order"]
        verbose_name = "Quiz Question"
        verbose_name_plural = "Quiz Questions"

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"

    def get_options(self):
        return [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
        ]

    @property
    def get_image_url(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url

    @property
    def get_audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        return self.audio_url


class QuizAttempt(models.Model):
    """Records a student's attempt at a quiz."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="quiz_attempts", verbose_name="Student"
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="Quiz"
    )
    score = models.PositiveIntegerField(default=0, verbose_name="Skor")
    total_questions = models.PositiveIntegerField(default=0, verbose_name="Total Soal")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}: {self.score}/{self.total_questions}"

    @property
    def percentage(self):
        if self.total_questions <= 0:
            return 0
        return round((self.score / self.total_questions) * 100)


class QuizAnswer(models.Model):
    """Individual answer in a quiz attempt."""
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers", verbose_name="Attempt"
    )
    question = models.ForeignKey(
        QuizQuestion, on_delete=models.CASCADE, verbose_name="Question"
    )
    selected_answer = models.CharField(max_length=1, verbose_name="Jawaban Dipilih")

    class Meta:
        verbose_name = "Quiz Answer"
        verbose_name_plural = "Quiz Answers"

    @property
    def is_correct(self):
        return self.selected_answer == self.question.correct_answer


# =============================================
# ASSIGNMENT SYSTEM
# =============================================

class Assignment(models.Model):
    """An assignment/task belongs to a course."""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments", verbose_name="Course"
    )
    title = models.CharField(max_length=255, verbose_name="Judul Tugas")
    description = models.TextField(blank=True, verbose_name="Deskripsi / Instruksi")
    attachment = models.FileField(
        upload_to="assignments/files/",
        blank=True, null=True,
        verbose_name="File Soal",
        help_text="Upload file soal tugas (PDF, dll.)"
    )
    deadline = models.DateTimeField(blank=True, null=True, verbose_name="Batas Waktu")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class AssignmentSubmission(models.Model):
    """Student's submission for an assignment."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="assignment_submissions", verbose_name="Student"
    )
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE,
        related_name="submissions", verbose_name="Assignment"
    )
    file = models.FileField(
        upload_to="assignments/submissions/",
        blank=True,
        null=True,
        verbose_name="File Jawaban"
    )
    audio_file = models.FileField(
        upload_to="assignments/submissions/audio/",
        blank=True,
        null=True,
        verbose_name="File Audio Jawaban"
    )
    link_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Link/URL Jawaban"
    )
    notes = models.TextField(blank=True, verbose_name="Catatan Siswa")
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.PositiveIntegerField(blank=True, null=True, verbose_name="Nilai (0-100)")
    feedback = models.TextField(blank=True, verbose_name="Feedback Pengajar")

    class Meta:
        unique_together = ["student", "assignment"]
        ordering = ["-submitted_at"]
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

# =============================================
# LIVE SESSION MODELS
# =============================================

class LiveSession(models.Model):
    """A live virtual face-to-face session for a course."""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="live_sessions", verbose_name="Kursus"
    )
    title = models.CharField(max_length=255, verbose_name="Judul Pertemuan")
    meeting_link = models.URLField(max_length=500, verbose_name="Link Pertemuan (GMeet/Zoom)")
    start_time = models.DateTimeField(verbose_name="Waktu Mulai")
    end_time = models.DateTimeField(verbose_name="Waktu Selesai")
    description = models.TextField(blank=True, verbose_name="Deskripsi/Catatan")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Live Session"
        verbose_name_plural = "Live Sessions"

    def __str__(self):
        return f"{self.title} ({self.course.title})"

# =============================================
# ANNOUNCEMENT MODELS
# =============================================

class Announcement(models.Model):
    """Global announcements for all students."""
    title = models.CharField(max_length=255, verbose_name="Judul Pengumuman")
    file = models.FileField(upload_to="announcements/files/", blank=True, null=True, verbose_name="File Lampiran")
    link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Tautan (Link) Eksternal")
    is_active = models.BooleanField(default=True, verbose_name="Tampilkan")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Terbit")

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Pengumuman"
        verbose_name_plural = "Pengumuman"

    def __str__(self):
        return self.title
