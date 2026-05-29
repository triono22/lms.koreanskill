from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views import View
from .forms import ProfileEditForm


class ProfileView(LoginRequiredMixin, View):
    """View and edit user profile."""

    def get(self, request):
        form = ProfileEditForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, 'courses/profile.html', {
            'form': form,
            'password_form': password_form,
        })

    def post(self, request):
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '🔒 Password berhasil diubah!')
                return redirect('profile')
            form = ProfileEditForm(instance=request.user)
            return render(request, 'courses/profile.html', {
                'form': form,
                'password_form': password_form,
            })
        else:
            form = ProfileEditForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Profil berhasil diperbarui!')
                return redirect('profile')
            password_form = PasswordChangeForm(user=request.user)
            return render(request, 'courses/profile.html', {
                'form': form,
                'password_form': password_form,
            })

def custom_logout(request):
    """Handle logout via GET request."""
    logout(request)
    return redirect('login')
