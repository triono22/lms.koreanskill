from django.urls import path
from .views import UpdateProgressAPIView

urlpatterns = [
    path("api/update/<int:lesson_id>/", UpdateProgressAPIView.as_view(), name="update-progress-api"),
]
