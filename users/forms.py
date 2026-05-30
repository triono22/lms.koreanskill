from django import forms
from .models import User


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all',
                'placeholder': 'Nama Depan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all',
                'placeholder': 'Nama Belakang'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all',
                'placeholder': 'email@example.com'
            }),
        }

class AdminUserCreationForm(forms.ModelForm):
    """Custom form for creating users in the admin panel easily."""
    tanggal_lahir = forms.DateField(
        label="Tanggal Lahir",
        help_text="Gunakan date picker. Akan dijadikan password default dengan format DDMMYYYY.",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Generate username dari nama depan
        first_name_clean = self.cleaned_data['first_name'].lower().replace(' ', '')
        base_username = first_name_clean
        counter = 1
        while User.objects.filter(username=base_username).exists():
            base_username = f"{first_name_clean}{counter}"
            counter += 1
        user.username = base_username
        
        # Set password dari tanggal lahir (DDMMYYYY)
        tanggal_lahir = self.cleaned_data['tanggal_lahir']
        password = tanggal_lahir.strftime('%d%m%Y')
        user.set_password(password)
        
        if commit:
            user.save()
        return user
