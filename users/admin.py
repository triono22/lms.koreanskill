from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from .forms import AdminUserCreationForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role field."""
    add_form = AdminUserCreationForm

    list_display = ("username", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("LMS Role", {"fields": ("role",)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'tanggal_lahir', 'role'),
        }),
    )
