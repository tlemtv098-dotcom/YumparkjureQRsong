import pathlib
p = pathlib.Path(r"D:\mysong\music\views.py")
t = p.read_text(encoding="utf-8")

old = """        artwork = str(data.get('artwork', '')).strip()[:500]
        client_id = str(client_id).strip()[:64]
        
        song = SongQueue.objects.create("""
new = """        artwork_data = data.get('artwork', '')
        artwork_file = None
        if artwork_data and artwork_data.startswith('data:image/'):
            import base64, uuid
            try:
                header, b64data = artwork_data.split(',', 1)
                ext = header.split('/')[1].split(';')[0]
                filename = f'{uuid.uuid4().hex}.{ext}'
                from django.core.files.base import ContentFile
                artwork_file = ContentFile(base64.b64decode(b64data), name=filename)
            except Exception:
                artwork_file = None
        
        artwork = artwork_file
        client_id = str(client_id).strip()[:64]
        
        song = SongQueue.objects.create("""
assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
print("Fix1 ok")

old2 = """        artwork = str(data.get('artwork', '')).strip()[:500]
        client_id = str(client_id).strip()[:64]
        
        # Get current first song position
        first_song = SongQueue.objects.filter(is_played=False).order_by('created_at').first()
        
        if first_song:
            # Insert before first song by setting created_at slightly earlier
            new_song = SongQueue.objects.create(
                title=title,
                video_id=video_id,
                thumbnail=thumbnail,
                channel=channel,
                audio_url=audio_url,
                artwork=artwork,
                requested_by=requested_by,
                client_id=client_id,
                created_at=first_song.created_at - timedelta(seconds=1)
            )"""
new2 = """        artwork_data = data.get('artwork', '')
        artwork_file = None
        if artwork_data and artwork_data.startswith('data:image/'):
            import base64, uuid
            try:
                header, b64data = artwork_data.split(',', 1)
                ext = header.split('/')[1].split(';')[0]
                filename = f'{uuid.uuid4().hex}.{ext}'
                from django.core.files.base import ContentFile
                artwork_file = ContentFile(base64.b64decode(b64data), name=filename)
            except Exception:
                artwork_file = None
        
        artwork = artwork_file
        client_id = str(client_id).strip()[:64]
        
        # Get current first song position
        first_song = SongQueue.objects.filter(is_played=False).order_by('created_at').first()
        
        if first_song:
            # Insert before first song by setting created_at slightly earlier
            new_song = SongQueue.objects.create(
                title=title,
                video_id=video_id,
                thumbnail=thumbnail,
                channel=channel,
                audio_url=audio_url,
                artwork=artwork,
                requested_by=requested_by,
                client_id=client_id,
                created_at=first_song.created_at - timedelta(seconds=1)
            )"""
assert t.count(old2) == 1, "count=%d" % t.count(old2)
t = t.replace(old2, new2)
print("Fix2 ok")

p.write_text(t, encoding="utf-8")
print("ALL FIXES APPLIED")
