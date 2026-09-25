from django.contrib.auth.models import User
from django.db import models
from django.conf import settings


class Profile(models.Model):
    """User profile with role and avatar"""
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("customer", "Customer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == "admin"

    def is_staff_role(self):
        return self.role in ["admin", "staff"]

    def can_manage_users(self):
        return self.role == "admin"

    def can_manage_playlists(self):
        return self.role in ["admin", "staff"]


class Genre(models.Model):
    """Music genre for categorizing songs"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag for flexible song categorization"""
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    songs = models.JSONField(default=list, blank=True)
    genres = models.ManyToManyField(Genre, blank=True, related_name="playlists")
    tags = models.ManyToManyField(Tag, blank=True, related_name="playlists")
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}/{self.name}"


class BlockedVideo(models.Model):
    video_id = models.CharField(max_length=50, unique=True)
    reason = models.CharField(max_length=100, default="Error 153")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.video_id


class GoodVideo(models.Model):
    video_id = models.CharField(max_length=50, unique=True)
    plays = models.IntegerField(default=0)
    title = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.video_id


class SongQueue(models.Model):
    title = models.CharField(max_length=255)
    video_id = models.CharField(max_length=50)
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
    channel = models.CharField(max_length=255, blank=True, null=True)
    audio_url = models.URLField(max_length=1000, blank=True, null=True)
    artwork = models.ImageField(upload_to="artwork/", blank=True, null=True)
    requested_by = models.CharField(max_length=100, default="ลูกค้าในร้าน")
    client_id = models.CharField(max_length=64, blank=True, default="")
    is_played = models.BooleanField(default=False)
    genres = models.ManyToManyField(Genre, blank=True, related_name="queued_songs")
    tags = models.ManyToManyField(Tag, blank=True, related_name="queued_songs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class ClientLog(models.Model):
    session = models.CharField(max_length=64, blank=True)
    ua = models.CharField(max_length=300, blank=True)
    event = models.CharField(max_length=64)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# Signal to create profile automatically
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
