import csv
import io
import os
import tempfile
import urllib.request
from urllib.parse import urlparse

from django.core.files import File
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path
from django.utils.safestring import mark_safe

from .models import (
    Course, Lesson, Enrollment,
    Quiz, QuizQuestion, QuizAttempt, QuizAnswer,
    Assignment, AssignmentSubmission,
    LiveSession, Announcement,
)


class LessonInline(admin.TabularInline):
    """Inline editor for lessons inside a course."""
    model = Lesson
    extra = 1
    fields = ("order", "title", "video_url", "video_file", "attachment", "total_duration")
    ordering = ("order",)


class QuizQuestionInline(admin.TabularInline):
    """Inline editor for quiz questions."""
    model = QuizQuestion
    extra = 1
    fields = ("order", "question_text", "audio_file", "audio_url", "image_file", "image_url", "option_a", "option_b", "option_c", "option_d", "correct_answer")
    ordering = ("order",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "created_at", "updated_at")
    list_filter = ("teacher",)
    search_fields = ("title", "description")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "total_duration", "video_url", "attachment")
    list_filter = ("course",)
    search_fields = ("title",)
    ordering = ("course", "order")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at", "is_active")
    list_filter = ("is_active", "course")
    search_fields = ("student__username", "course__title")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "question_count", "deadline", "is_active", "created_at")
    list_filter = ("is_active", "course")
    search_fields = ("title",)
    inlines = [QuizQuestionInline]
    change_form_template = "admin/courses/quiz/change_form.html"

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Jumlah Soal"

    def get_urls(self):
        custom_urls = [
            path(
                "<int:quiz_id>/upload-csv/",
                self.admin_site.admin_view(self.upload_csv_view),
                name="courses_quiz_upload_csv",
            ),
            path(
                "download-csv-template/",
                self.admin_site.admin_view(self.download_csv_template),
                name="courses_quiz_download_template",
            ),
        ]
        return custom_urls + super().get_urls()

    def download_csv_template(self, request):
        """Download an empty CSV template with correct headers."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="quiz_template.csv"'
        response.write('\ufeff')  # BOM for Excel UTF-8 compatibility
        writer = csv.writer(response)
        writer.writerow(["question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "order", "audio_file", "audio_url", "image_file", "image_url"])
        writer.writerow(["Apa arti 안녕하세요?", "Selamat tinggal", "Selamat pagi/siang/malam", "Terima kasih", "Maaf", "B", "1", "", "", "", ""])
        writer.writerow(["Huruf Korea disebut?", "Kanji", "Hiragana", "Hangul", "Romaji", "C", "2", "", "", "", ""])
        return response

    def upload_csv_view(self, request, quiz_id):
        """Handle CSV upload for bulk question creation."""
        quiz = get_object_or_404(Quiz, pk=quiz_id)

        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")

            if not csv_file:
                messages.error(request, "Silakan pilih file CSV.")
                return redirect(request.path)

            if not csv_file.name.endswith(".csv"):
                messages.error(request, "File harus berformat .csv")
                return redirect(request.path)

            try:
                decoded = csv_file.read().decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(decoded))

                required_cols = {"question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer"}
                if not required_cols.issubset(set(reader.fieldnames or [])):
                    missing = required_cols - set(reader.fieldnames or [])
                    messages.error(
                        request,
                        f"Kolom CSV tidak lengkap. Kolom yang hilang: {', '.join(missing)}"
                    )
                    return redirect(request.path)

                # Determine starting order
                last_order = quiz.questions.order_by("-order").values_list("order", flat=True).first() or 0

                created_count = 0
                errors = []
                for i, row in enumerate(reader, start=1):
                    answer = row.get("correct_answer", "").strip().upper()
                    if answer not in ("A", "B", "C", "D"):
                        errors.append(f"Baris {i}: correct_answer '{row.get('correct_answer', '')}' tidak valid (harus A/B/C/D)")
                        continue

                    question_text = row.get("question_text", "").strip()
                    if not question_text:
                        errors.append(f"Baris {i}: question_text kosong, dilewati.")
                        continue

                    order_val = row.get("order", "").strip()
                    if order_val:
                        try:
                            order_num = int(order_val)
                        except ValueError:
                            last_order += 1
                            order_num = last_order
                    else:
                        last_order += 1
                        order_num = last_order

                    # Create QuizQuestion first
                    question = QuizQuestion.objects.create(
                        quiz=quiz,
                        question_text=question_text,
                        option_a=row.get("option_a", "").strip(),
                        option_b=row.get("option_b", "").strip(),
                        option_c=row.get("option_c", "").strip(),
                        option_d=row.get("option_d", "").strip(),
                        correct_answer=answer,
                        order=order_num,
                    )
                    
                    # Handle audio file/URL (Support read-only URL reference directly)
                    audio_val = row.get("audio_file", "").strip()
                    audio_url_val = row.get("audio_url", "").strip()
                    
                    if audio_val:
                        if audio_val.startswith("http://") or audio_val.startswith("https://"):
                            question.audio_url = audio_val
                        else:
                            # Local relative file path
                            question.audio_file = audio_val
                    
                    if audio_url_val:
                        question.audio_url = audio_url_val

                    # Handle image file/URL (Support read-only URL reference directly)
                    image_val = row.get("image_file", "").strip()
                    image_url_val = row.get("image_url", "").strip()
                    
                    if image_val:
                        if image_val.startswith("http://") or image_val.startswith("https://"):
                            question.image_url = image_val
                        else:
                            # Local relative file path
                            question.image_file = image_val
                    
                    if image_url_val:
                        question.image_url = image_url_val

                    question.save()
                    created_count += 1

                if created_count > 0:
                    messages.success(request, f"✅ Berhasil mengimport {created_count} soal ke kuis \"{quiz.title}\".")
                if errors:
                    messages.warning(request, "⚠️ Beberapa baris dilewati:\n" + "\n".join(errors))

            except Exception as e:
                messages.error(request, f"Gagal membaca CSV: {str(e)}")
                return redirect(request.path)

            return redirect(f"../../{quiz_id}/change/")

        # GET: show upload form
        context = {
            **self.admin_site.each_context(request),
            "quiz": quiz,
            "opts": self.model._meta,
            "title": f"Upload CSV Soal — {quiz.title}",
        }
        return render(request, "admin/courses/quiz/upload_csv.html", context)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "question_text", "audio_file", "audio_url", "image_file", "image_url", "correct_answer")
    list_filter = ("quiz",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "total_questions", "submitted_at")
    list_filter = ("quiz",)
    readonly_fields = ("student", "quiz", "score", "total_questions", "submitted_at")


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_answer")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "deadline", "is_active", "created_at")
    list_filter = ("is_active", "course")
    search_fields = ("title",)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "submitted_at", "grade", "has_file", "has_audio", "has_link")
    list_filter = ("assignment",)
    search_fields = ("student__username",)
    readonly_fields = ("student", "assignment", "submitted_at", "display_file", "display_audio", "display_link")
    fields = ("student", "assignment", "notes", "display_file", "display_audio", "display_link", "submitted_at", "grade", "feedback")

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = "File"

    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = "Audio"

    def has_link(self, obj):
        return bool(obj.link_url)
    has_link.boolean = True
    has_link.short_description = "Link"

    def display_file(self, obj):
        if obj.file:
            return mark_safe(f'<a href="{obj.file.url}" target="_blank" style="background: #2563eb; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 11px;">Unduh/Buka File Dokumen</a>')
        return "Tidak ada file dokumen"
    display_file.short_description = "Jawaban Dokumen"

    def display_audio(self, obj):
        if obj.audio_file:
            return mark_safe(f'<audio controls style="height: 32px;"><source src="{obj.audio_file.url}" type="audio/mpeg">Browser Anda tidak mendukung audio player.</audio>')
        return "Tidak ada audio"
    display_audio.short_description = "Jawaban Audio"

    def display_link(self, obj):
        if obj.link_url:
            return mark_safe(f'<a href="{obj.link_url}" target="_blank" style="font-weight: bold; color: #2563eb;">{obj.link_url} ↗</a>')
        return "Tidak ada link"
    display_link.short_description = "Jawaban Link/URL"


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "start_time", "end_time", "is_active")
    list_filter = ("course", "is_active", "start_time")
    search_fields = ("title", "course__title")
    date_hierarchy = "start_time"
    ordering = ("-start_time",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_active", "has_file", "has_link")
    list_filter = ("is_active", "published_at")
    search_fields = ("title",)

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = "File"

    def has_link(self, obj):
        return bool(obj.link)
    has_link.boolean = True
    has_link.short_description = "Link"
