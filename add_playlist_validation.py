import pathlib
p = pathlib.Path(r"D:\mysong\music\forms.py")
t = p.read_text(encoding="utf-8")

# Add validation to PlaylistForm
old_playlist = """    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Playlist.objects.filter(name=name).exists():
            raise ValidationError("ชื่อเพลย์ลิสต์นี้มีอยู่แล้ว")
        return name


class GenreForm(forms.ModelForm):"""

new_playlist = """    def clean_name(self):
        name = self.cleaned_data.get("name")
        if Playlist.objects.filter(user=self.instance.user, name=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError("คุณมีเพลย์ลิสต์ชื่อนี้อยู่แล้ว")
        return name

    def clean_songs(self):
        songs = self.cleaned_data.get("songs")
        if songs:
            if not isinstance(songs, list):
                raise ValidationError("songs ต้องเป็น list")
            for i, song in enumerate(songs):
                if not isinstance(song, dict):
                    raise ValidationError(f"เพลงที่ {i+1} ต้องเป็น object")
                required = ["id", "title", "video_id"]
                for field in required:
                    if field not in song:
                        raise ValidationError(f"เพลงที่ {i+1} ขาด field: {field}")
        return songs


class GenreForm(forms.ModelForm):"""

assert t.count(old_playlist) == 1, "count=%d" % t.count(old_playlist)
t = t.replace(old_playlist, new_playlist)
print("PlaylistForm validation added")

p.write_text(t, encoding="utf-8")
print("PlaylistForm validation added")
