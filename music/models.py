from django.contrib.auth.models import User
from django.db import models

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=100)
    songs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}/{self.name}"

class BlockedVideo(models.Model):
    video_id = models.CharField(max_length=50, unique=True)
    reason = models.CharField(max_length=100, default='Error 153')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.video_id

class SongQueue(models.Model):
    title = models.CharField(max_length=255)
    video_id = models.CharField(max_length=50)
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
    channel = models.CharField(max_length=255, blank=True, null=True)
    audio_url = models.URLField(max_length=1000, blank=True, null=True)
    requested_by = models.CharField(max_length=100, default="ลูกค้าในร้าน")
    client_id = models.CharField(max_length=64, blank=True, default='')
    is_played = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title

class ClientLog(models.Model):
    session = models.CharField(max_length=64, blank=True)
    ua = models.CharField(max_length=300, blank=True)
    event = models.CharField(max_length=64)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
