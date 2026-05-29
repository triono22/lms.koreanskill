from django.urls import path
from django.contrib.auth.views import LoginView
from .views import ProfileView, custom_logout

urlpatterns = [
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
