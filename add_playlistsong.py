import pathlib
p = pathlib.Path(r"D:\mysong\music\models.py")
t = p.read_text(encoding="utf-8")

old = """    def __str__(self):
        return f"{self.user.username}/{self.name}"


class BlockedVideo(models.Model):"""

new = """    def __str__(self):
        return f"{self.user.username}/{self.name}"

    def get_songs_ordered(self):
        return [ps.song for ps in self.playlist_songs.select_related("song").order_by("position")]

    def add_song(self, song, position=None):
        if self.songs.filter(id=song.id).exists():
            return False
        if position is None:
            position = self.playlist_songs.count()
        PlaylistSong.objects.create(playlist=self, song=song, position=position)
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
        ps.position = new_position
        ps.save(update_fields=["position"])
        if new_position < ps.position:
            PlaylistSong.objects.filter(
                playlist=self, position__gte=new_position, position__lt=ps.position
            ).exclude(id=ps.id).update(position=models.F("position") + 1)
        else:
            PlaylistSong.objects.filter(
                playlist=self, position__gt=ps.position, position__lte=new_position
            ).exclude(id=ps.id).update(position=models.F("position") - 1)
        return True


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="playlist_songs")
    song = models.ForeignKey(SongQueue, on_delete=models.CASCADE, related_name="playlist_entries")
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]
        unique_together = ("playlist", "song")

    def __str__(self):
        return f"{self.playlist.name} - {self.song.title} (pos {self.position})"


class BlockedVideo(models.Model):"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("PlaylistSong through model added")
