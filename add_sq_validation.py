import pathlib
p = pathlib.Path(r"D:\mysong\music\forms.py")
t = p.read_text(encoding="utf-8")

# Add validation to SongQueueForm
old_sq = """    def clean_video_id(self):
        video_id = self.cleaned_data.get("video_id")
        if video_id and len(video_id) != 11:
            raise ValidationError("Video ID ต้องมี 11 ตัวอักษร")
        return video_id


class GenreForm(forms.ModelForm):"""

new_sq = """    def clean_video_id(self):
        video_id = self.cleaned_data.get("video_id")
        if video_id and len(video_id) != 11:
            raise ValidationError("Video ID ต้องมี 11 ตัวอักษร")
        if video_id and not video_id.isalnum() and "-" not in video_id and "_" not in video_id:
            raise ValidationError("Video ID ต้องเป็นตัวอักษร ตัวเลข - หรือ _ เท่านั้น")
        return video_id

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if thumbnail and not thumbnail.startswith(("http://", "https://")):
            raise ValidationError("Thumbnail ต้องเป็น URL ที่ถูกต้อง")
        return thumbnail

    def clean_audio_url(self):
        audio_url = self.cleaned_data.get("audio_url")
        if audio_url and not audio_url.startswith(("http://", "https://")):
            raise ValidationError("Audio URL ต้องเป็น URL ที่ถูกต้อง")
        return audio_url


class GenreForm(forms.ModelForm):"""

assert t.count(old_sq) == 1, "count=%d" % t.count(old_sq)
t = t.replace(old_sq, new_sq)
print("SongQueueForm validation added")

p.write_text(t, encoding="utf-8")
print("SongQueueForm validation added")
