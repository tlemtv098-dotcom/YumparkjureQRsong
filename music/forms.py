from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, Playlist, Genre, Tag, SongQueue


class RegisterForm(UserCreationForm):
    """User registration form with email and role"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            "placeholder": "อีเมล"
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            "placeholder": "ชื่อ"
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            "placeholder": "นามสกุล"
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            "placeholder": "เบอร์โทร (ไม่บังคับ)"
        })
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อผู้ใช้ (อังกฤษ/ตัวเลข)"
            }),
            "password1": forms.PasswordInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "รหัสผ่าน"
            }),
            "password2": forms.PasswordInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ยืนยันรหัสผ่าน"
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Profile update form"""
    class Meta:
        model = Profile
        fields = ("avatar", "phone")
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "accept": "image/*"
            }),
            "phone": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "เบอร์โทร"
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.replace("-", "").replace(" ", "").isdigit():
            raise ValidationError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return phone


class UserForm(forms.ModelForm):
    """User basic info form for admin"""
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 text-amber-500 border-slate-300 rounded focus:ring-amber-400"
            }),
        }


class ProfileRoleForm(forms.ModelForm):
    """Role assignment form for admin"""
    class Meta:
        model = Profile
        fields = ("role",)
        widgets = {
            "role": forms.Select(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
            }),
        }


class PlaylistForm(forms.ModelForm):
    """Playlist create/edit form"""
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            "class": "space-y-2"
        })
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            "class": "space-y-2"
        })
    )

    class Meta:
        model = Playlist
        fields = ("name", "description", "genres", "tags", "is_public")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อเพลย์ลิสต์"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "คำอธิบาย (ไม่บังคับ)",
                "rows": 3
            }),
            "is_public": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 text-amber-500 border-slate-300 rounded focus:ring-amber-400"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Playlist.objects.filter(name=name).exists():
            raise ValidationError("ชื่อเพลย์ลิสต์นี้มีอยู่แล้ว")
        return name


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อแนวเพลง"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "คำอธิบาย",
                "rows": 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Genre.objects.filter(name__iexact=name).exists():
            raise ValidationError("แนวเพลงนี้มีอยู่แล้ว")
        return name


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อแท็ก"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Tag.objects.filter(name__iexact=name).exists():
            raise ValidationError("แท็กนี้มีอยู่แล้ว")
        return name


class SongQueueForm(forms.ModelForm):
    """Song queue form for staff"""
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"})
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"})
    )

    class Meta:
        model = SongQueue
        fields = ("title", "video_id", "thumbnail", "channel", "genres", "tags")
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อเพลง"
            }),
            "video_id": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "YouTube Video ID (11 ตัวอักษร)"
            }),
            "thumbnail": forms.URLInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "URL รูปภาพ thumbnail"
            }),
            "channel": forms.TextInput(attrs={
                "class": "w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400",
                "placeholder": "ชื่อช่อง/ศิลปิน"
            }),
        }

    def clean_video_id(self):
        video_id = self.cleaned_data.get("video_id")
        if video_id and len(video_id) != 11:
            raise ValidationError("Video ID ต้องมี 11 ตัวอักษร")
        return video_id
