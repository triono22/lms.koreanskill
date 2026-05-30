from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import generics
from django.contrib import messages

from .models import (
    Course, Enrollment, Lesson,
    Quiz, QuizQuestion, QuizAttempt, QuizAnswer,
    Assignment, AssignmentSubmission,
    LiveSession, Announcement,
)
from .serializers import CourseSerializer
from attendance.models import LessonProgress


def format_duration(seconds):
    """Convert seconds to Xm Ys format."""
    if seconds <= 0:
        return "0m 0s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


# --- Template Views ---

class LandingPageView(View):
    """Public landing page for non-authenticated visitors."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('student-dashboard')
        from users.models import User
        context = {
            'courses': Course.objects.all()[:6],
            'total_courses': Course.objects.count(),
            'total_students': User.objects.filter(role='STUDENT').count(),
            'total_lessons': Lesson.objects.count(),
            'total_quizzes': Quiz.objects.count(),
        }
        return render(request, 'landing_page.html', context)



class CourseDetailPublicView(LoginRequiredMixin, DetailView):
    """View course details before enrolling."""
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all().order_by('order')
        context['quiz_count'] = self.object.quizzes.filter(is_active=True).count()
        context['assignment_count'] = self.object.assignments.filter(is_active=True).count()
        context['is_enrolled'] = Enrollment.objects.filter(
            student=self.request.user, course=self.object
        ).exists()
        total_seconds = sum(l.total_duration for l in context['lessons'])
        context['total_duration'] = format_duration(total_seconds)
        context['format_duration'] = format_duration
        return context


class AllCoursesView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        # Ambil kursus yang mahasiswa BELUM daftar
        enrolled_course_ids = Enrollment.objects.filter(
            student=self.request.user
        ).values_list('course_id', flat=True)
        
        query = self.request.GET.get('q')
        queryset = Course.objects.exclude(id__in=enrolled_course_ids)
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        return queryset


class EnrollActionView(LoginRequiredMixin, View):
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        _, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'is_active': True}
        )
        if created:
            messages.success(request, f'🎉 Berhasil mendaftar kursus "{course.title}"!')
        return redirect('student-dashboard')

class StudentDashboardView(LoginRequiredMixin, ListView):
    model = Enrollment
    template_name = "courses/dashboard.html"
    context_object_name = "enrollments"

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollments = context["enrollments"]
        total_progress = 0
        
        for enrollment in enrollments:
            course = enrollment.course
            first_lesson = course.lessons.order_by('order').first()
            enrollment.first_lesson_id = first_lesson.id if first_lesson else None
            
            total_duration = course.lessons.aggregate(Sum('total_duration'))['total_duration__sum'] or 0
            
            if total_duration > 0:
                watched = LessonProgress.objects.filter(
                    student=self.request.user,
                    lesson__course=course
                ).aggregate(Sum('watched_duration'))['watched_duration__sum'] or 0
                
                enrollment.overall_progress = min(int((float(watched) / total_duration) * 100), 100)
            else:
                enrollment.overall_progress = 0
            total_progress += enrollment.overall_progress
        
        # Stats
        context["completed_lessons"] = LessonProgress.objects.filter(
            student=self.request.user, is_completed=True
        ).count()
        
        enrollment_count = len(enrollments)
        context["avg_progress"] = round(total_progress / enrollment_count) if enrollment_count > 0 else 0
        
        context["quiz_count"] = QuizAttempt.objects.filter(
            student=self.request.user
        ).count()
        
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "courses/lesson_detail.html"
    context_object_name = "lesson"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ambil data progres yang sudah ada (jika ada)
        progress = LessonProgress.objects.filter(
            student=self.request.user, 
            lesson=self.object
        ).first()
        context["current_progress"] = progress
        # Ambil daftar materi lain di course yang sama untuk sidebar
        context["all_lessons"] = self.object.course.lessons.all().order_by('order')
        return context


# --- Quiz Views ---

class MyQuizListView(LoginRequiredMixin, ListView):
    """Show all quizzes from enrolled courses."""
    template_name = "courses/quiz_list.html"
    context_object_name = "quizzes"

    def get_queryset(self):
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).values_list('course_id', flat=True)
        return Quiz.objects.filter(course_id__in=enrolled_courses, is_active=True, quiz_type='quiz')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempted_quiz_ids = QuizAttempt.objects.filter(
            student=self.request.user
        ).values_list('quiz_id', flat=True)
        context['attempted_quiz_ids'] = list(attempted_quiz_ids)
        context['page_title'] = 'Kuis'
        return context

class MyExamListView(LoginRequiredMixin, ListView):
    """Show all exams from enrolled courses."""
    template_name = "courses/quiz_list.html"
    context_object_name = "quizzes"

    def get_queryset(self):
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).values_list('course_id', flat=True)
        return Quiz.objects.filter(course_id__in=enrolled_courses, is_active=True, quiz_type='exam')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempted_quiz_ids = QuizAttempt.objects.filter(
            student=self.request.user
        ).values_list('quiz_id', flat=True)
        context['attempted_quiz_ids'] = list(attempted_quiz_ids)
        context['page_title'] = 'Ujian'
        context['is_exam'] = True
        return context


class MyListeningListView(LoginRequiredMixin, ListView):
    """Show all listening quizzes from enrolled courses."""
    template_name = "courses/quiz_list.html"
    context_object_name = "quizzes"

    def get_queryset(self):
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).values_list('course_id', flat=True)
        return Quiz.objects.filter(course_id__in=enrolled_courses, is_active=True, quiz_type='listening')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempted_quiz_ids = QuizAttempt.objects.filter(
            student=self.request.user
        ).values_list('quiz_id', flat=True)
        context['attempted_quiz_ids'] = list(attempted_quiz_ids)
        context['page_title'] = 'Listening'
        return context


class QuizDetailView(LoginRequiredMixin, DetailView):
    """Display quiz questions for the student to answer."""
    model = Quiz
    template_name = "courses/quiz_detail.html"
    context_object_name = "quiz"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order')
        # Check if already attempted
        context['already_attempted'] = QuizAttempt.objects.filter(
            student=self.request.user, quiz=self.object
        ).exists()
        return context


class QuizSubmitView(LoginRequiredMixin, View):
    """Process quiz submission and calculate score."""

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        questions = quiz.questions.all()
        
        # Prevent re-submission
        if QuizAttempt.objects.filter(student=request.user, quiz=quiz).exists():
            return redirect('quiz-result', pk=QuizAttempt.objects.filter(
                student=request.user, quiz=quiz
            ).first().pk)
        
        # Create attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            total_questions=questions.count()
        )
        
        score = 0
        for question in questions:
            selected = request.POST.get(f'question_{question.id}', '')
            QuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected
            )
            if selected == question.correct_answer:
                score += 1
        
        attempt.score = score
        attempt.save()
        
        pct = attempt.percentage
        if pct >= 80:
            messages.success(request, f'🎉 Luar biasa! Skor Anda: {pct}%')
        elif pct >= 60:
            messages.info(request, f'👍 Bagus! Skor Anda: {pct}%')
        else:
            messages.warning(request, f'📚 Skor Anda: {pct}%. Tetap semangat belajar!')
        
        return redirect('quiz-result', pk=attempt.pk)


class QuizResultView(LoginRequiredMixin, DetailView):
    """Show quiz results with answers."""
    model = QuizAttempt
    template_name = "courses/quiz_result.html"
    context_object_name = "attempt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.all().select_related('question')
        context['wrong_count'] = self.object.total_questions - self.object.score
        return context


# --- Assignment Views ---

class MyAssignmentListView(LoginRequiredMixin, ListView):
    """Show all assignments from enrolled courses."""
    template_name = "courses/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).values_list('course_id', flat=True)
        return Assignment.objects.filter(course_id__in=enrolled_courses, is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submitted_ids = AssignmentSubmission.objects.filter(
            student=self.request.user
        ).values_list('assignment_id', flat=True)
        context['submitted_ids'] = list(submitted_ids)
        return context


class AssignmentSubmitView(LoginRequiredMixin, View):
    """Submit an assignment."""

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        existing = AssignmentSubmission.objects.filter(
            student=request.user, assignment=assignment
        ).first()
        return render(request, 'courses/assignment_submit.html', {
            'assignment': assignment,
            'submission': existing,
        })

    def post(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        
        # Prevent re-submission
        if AssignmentSubmission.objects.filter(student=request.user, assignment=assignment).exists():
            messages.info(request, 'Anda sudah mengumpulkan tugas ini.')
            return redirect('assignment-list')
        
        file = request.FILES.get('file')
        audio_file = request.FILES.get('audio_file')
        link_url = request.POST.get('link_url', '').strip()
        notes = request.POST.get('notes', '')
        
        # Validasi minimal salah satu jawaban terisi
        if not file and not audio_file and not link_url:
            messages.error(request, 'Silakan isi setidaknya satu jawaban: Upload File, Audio, atau masukkan Link URL.')
            return redirect(request.path)
            
        AssignmentSubmission.objects.create(
            student=request.user,
            assignment=assignment,
            file=file,
            audio_file=audio_file,
            link_url=link_url if link_url else None,
            notes=notes,
        )
        messages.success(request, f'✅ Tugas "{assignment.title}" berhasil dikumpulkan!')
        
        return redirect('assignment-list')


# --- API Views ---

class CourseListAPIView(generics.ListAPIView):
    """API untuk melihat daftar semua course."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseDetailAPIView(generics.RetrieveAPIView):
    """API untuk melihat detail satu course berdasarkan ID."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

# --- Grade View ---
class MyGradesView(LoginRequiredMixin, ListView):
    """Show student's quiz and exam attempts."""
    template_name = "courses/grade_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            student=self.request.user
        ).select_related('quiz', 'quiz__course')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nilai Saya'
        return context

# --- Live Session View ---
class MyLiveSessionListView(LoginRequiredMixin, ListView):
    """Show live sessions for enrolled courses."""
    template_name = "courses/live_session_list.html"
    context_object_name = "live_sessions"

    def get_queryset(self):
        enrolled_courses = Enrollment.objects.filter(
            student=self.request.user, is_active=True
        ).values_list('course_id', flat=True)
        return LiveSession.objects.filter(course_id__in=enrolled_courses, is_active=True).order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        context['now'] = timezone.now()
        return context

# --- Announcement View ---
class AnnouncementListView(LoginRequiredMixin, ListView):
    """Show global announcements to students."""
    template_name = "courses/announcement_list.html"
    context_object_name = "announcements"

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Pengumuman'
        return context



