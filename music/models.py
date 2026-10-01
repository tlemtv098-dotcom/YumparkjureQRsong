import uuid

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.text import slugify


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


def _mint_slug(model, name, prefix, max_length):
    """Build a slug for a name the create form never asks one for.

    ``slugify()`` drops every Thai character, so a genre named "เพลงรัก"
    slugifies to "". The slug column is unique, so the second Thai-only
    name raised IntegrityError and the create page returned a 500. Fall
    back to a short random token whenever the slugified name is empty.
    """
    base = slugify(name)[:max_length].strip("-")
    if not base:
        base = f"{prefix}-{uuid.uuid4().hex[:6]}"
    candidate = base
    while model.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{uuid.uuid4().hex[:4]}"
    return candidate


class Genre(models.Model):
    """Music genre for categorizing songs"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Keep the stored slug on edit; only mint one when it is empty.
        if not self.slug:
            self.slug = _mint_slug(Genre, self.name, "g", 50)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Tag for flexible song categorization"""
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=30, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _mint_slug(Tag, self.name, "t", 30)
        super().save(*args, **kwargs)


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

    def get_songs_ordered(self):
        return [ps.song for ps in self.playlist_songs.select_related("song").order_by("position")]

    def add_song(self, song, position=None):
        # Check if song already in playlist (via JSON field)
        song_ids = [s.get("id") for s in self.songs if isinstance(s, dict)]
        if song.id in song_ids:
            return False
        if position is None:
            position = self.playlist_songs.count()
        PlaylistSong.objects.create(playlist=self, song=song, position=position)
        # Also add to JSON field for backward compatibility
        self.songs.append({"id": song.id, "title": song.title, "video_id": song.video_id})
        self.save(update_fields=["songs"])
        return True

    def remove_song(self, song):
        deleted, _ = self.playlist_songs.filter(song=song).delete()
        if deleted:
            for i, ps in enumerate(self.playlist_songs.order_by("position")):
                ps.position = i
                ps.save(update_fields=["position"])
            return True
        return False

    def reorder_song(self, song, new_position):
        try:
            ps = self.playlist_songs.get(song=song)
        except PlaylistSong.DoesNotExist:
            return False
        old_position = ps.position
        if old_position == new_position:
            return True
        # Shift other songs
        if new_position < old_position:
            # Moving up: shift down songs in between
            PlaylistSong.objects.filter(
                playlist=self, position__gte=new_position, position__lt=old_position
            ).exclude(id=ps.id).update(position=models.F("position") + 1)
        else:
            # Moving down: shift up songs in between
            PlaylistSong.objects.filter(
                playlist=self, position__gt=old_position, position__lte=new_position
            ).exclude(id=ps.id).update(position=models.F("position") - 1)
        ps.position = new_position
        ps.save(update_fields=["position"])
        return True


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="playlist_songs")
    song = models.ForeignKey("SongQueue", on_delete=models.CASCADE, related_name="playlist_entries")
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        unique_together = ("playlist", "song")

    def __str__(self):
        return f"{self.playlist.name} - {self.song.title} (pos {self.position})"


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
    # Creation only, and there is deliberately no companion receiver that
    # re-saves instance.profile on every User save. Django caches a reverse
    # one-to-one on the instance the first time it is read, so such a
    # write-back resurrects the role='customer' copy cached here at creation
    # and silently reverts whatever the application has since saved. Login
    # triggers it: update_last_login saves the User. Nothing on User needs
    # propagating into Profile anyway -- role, phone and avatar are all
    # written to the Profile directly by the forms and the admin views.
    if created:
        Profile.objects.create(user=instance)
