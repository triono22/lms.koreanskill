from django.urls import path
from .views import (
    CourseListAPIView, CourseDetailAPIView,
    StudentDashboardView, LessonDetailView,
    AllCoursesView, EnrollActionView,
    CourseDetailPublicView,
    MyQuizListView, MyExamListView, QuizDetailView, QuizSubmitView, QuizResultView,
    MyAssignmentListView, AssignmentSubmitView,
    MyGradesView, MyLiveSessionListView, AnnouncementListView,
    MyListeningListView,
)

urlpatterns = [
    # Template Views
    path("list/", AllCoursesView.as_view(), name="course-list"),
    path("detail/<int:pk>/", CourseDetailPublicView.as_view(), name="course-detail"),
    path("enroll/<int:course_id>/", EnrollActionView.as_view(), name="enroll-action"),
    path("dashboard/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("my-announcements/", AnnouncementListView.as_view(), name="announcement-list"),
    path("lesson/<int:pk>/", LessonDetailView.as_view(), name="lesson-detail"),

    # Quiz & Exam Views
    path("my-quizzes/", MyQuizListView.as_view(), name="quiz-list"),
    path("my-exams/", MyExamListView.as_view(), name="exam-list"),
    path("my-listening/", MyListeningListView.as_view(), name="listening-list"),
    path("my-grades/", MyGradesView.as_view(), name="grade-list"),
    path("my-live-sessions/", MyLiveSessionListView.as_view(), name="live-list"),
    path("quiz/<int:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("quiz/<int:pk>/submit/", QuizSubmitView.as_view(), name="quiz-submit"),
    path("quiz/result/<int:pk>/", QuizResultView.as_view(), name="quiz-result"),

    # Assignment Views
    path("my-assignments/", MyAssignmentListView.as_view(), name="assignment-list"),
    path("assignment/<int:pk>/", AssignmentSubmitView.as_view(), name="assignment-submit"),

    # API Views
    path("api/", CourseListAPIView.as_view(), name="course-list-api"),
    path("api/<int:pk>/", CourseDetailAPIView.as_view(), name="course-detail-api"),
]
