import pathlib
p = pathlib.Path(r"D:\mysong\music\models.py")
t = p.read_text(encoding="utf-8")

# Fix reorder_song logic
old = """    def reorder_song(self, song, new_position):
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
        return True"""

new = """    def reorder_song(self, song, new_position):
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
        return True"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Fixed reorder_song")
