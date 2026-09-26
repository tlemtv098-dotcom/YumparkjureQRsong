import pathlib
p = pathlib.Path(r"D:\mysong\music\models.py")
t = p.read_text(encoding="utf-8")

# Fix add_song to check JSON field instead of queryset
old = """    def add_song(self, song, position=None):
        if self.songs.filter(id=song.id).exists():
            return False
        if position is None:
            position = self.playlist_songs.count()
        PlaylistSong.objects.create(playlist=self, song=song, position=position)
        return True"""

new = """    def add_song(self, song, position=None):
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
        return True"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Fixed add_song")
