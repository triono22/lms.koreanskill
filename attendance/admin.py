from django.contrib import admin

from .models import LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "formatted_watched_duration", "is_completed", "progress_display", "last_watched_at")
    list_filter = ("is_completed", "lesson__course")
    search_fields = ("student__username", "lesson__title")
    readonly_fields = ("progress_display",)

    @admin.display(description="Durasi Ditonton", ordering="watched_duration")
    def formatted_watched_duration(self, obj):
        if not obj.watched_duration:
            return "0m 0s"
        minutes, seconds = divmod(obj.watched_duration, 60)
        return f"{minutes}m {seconds}s"

    @admin.display(description="Progress (%)")
    def progress_display(self, obj):
        """Show watch progress as a percentage."""
        return f"{obj.progress_percentage:.0f}%"

from django.template.response import TemplateResponse
from courses.models import Course, Enrollment, QuizAttempt, AssignmentSubmission
from .models import StudentGradeRecord

@admin.register(StudentGradeRecord)
class StudentGradeRecordAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name_display', 'avg_quiz', 'avg_exam', 'avg_assignment')
    search_fields = ('username', 'first_name', 'last_name')

    def full_name_display(self, obj):
        return obj.get_full_name() or obj.username
    full_name_display.short_description = "Nama Siswa"

    def avg_quiz(self, obj):
        from django.db.models import Avg
        avg = QuizAttempt.objects.filter(student=obj, quiz__quiz_type='quiz').aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg is not None else "-"
    avg_quiz.short_description = "Rata-rata Kuis"

    def avg_exam(self, obj):
        from django.db.models import Avg
        avg = QuizAttempt.objects.filter(student=obj, quiz__quiz_type='exam').aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg is not None else "-"
    avg_exam.short_description = "Rata-rata Ujian"

    def avg_assignment(self, obj):
        from django.db.models import Avg
        avg = AssignmentSubmission.objects.filter(student=obj).aggregate(Avg('grade'))['grade__avg']
        return round(avg, 1) if avg is not None else "-"
    avg_assignment.short_description = "Rata-rata Tugas"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)
        
    def has_add_permission(self, request):
        return False
        
    def change_view(self, request, object_id, form_url='', extra_context=None):
        student = self.get_object(request, object_id)
        
        if student is None:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)
        
        # Get all enrolled courses for this student
        enrollments = Enrollment.objects.filter(student=student, is_active=True).select_related('course')
        
        courses_data = []
        for enrollment in enrollments:
            course = enrollment.course
            
            quizzes = QuizAttempt.objects.filter(student=student, quiz__course=course, quiz__quiz_type='quiz').select_related('quiz')
            exams = QuizAttempt.objects.filter(student=student, quiz__course=course, quiz__quiz_type='exam').select_related('quiz')
            assignments = AssignmentSubmission.objects.filter(student=student, assignment__course=course).select_related('assignment')
            
            courses_data.append({
                'course': course,
                'quizzes': quizzes,
                'exams': exams,
                'assignments': assignments,
            })
            
        context = dict(
            self.admin_site.each_context(request),
            title=f"Rekap Nilai: {student.get_full_name() or student.username}",
            student=student,
            courses_data=courses_data,
            opts=self.model._meta,
        )
        return TemplateResponse(request, "admin/attendance/studentgraderecord/change_form.html", context)
