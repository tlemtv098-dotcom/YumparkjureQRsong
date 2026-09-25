import pathlib
p = pathlib.Path(r"D:\mysong\music\views.py")
t = p.read_text(encoding="utf-8")

old1 = """        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
        audio_url = str(data.get('audio_url', '')).strip()[:1000]
        client_id = str(client_id).strip()[:64]
        
        song = SongQueue.objects.create(
            title=title,
            video_id=video_id,
            thumbnail=thumbnail,
            channel=channel,
            audio_url=audio_url,
            requested_by=requested_by,
            client_id=client_id
        )"""
new1 = """        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
        audio_url = str(data.get('audio_url', '')).strip()[:1000]
        artwork = str(data.get('artwork', '')).strip()[:500]
        client_id = str(client_id).strip()[:64]
        
        song = SongQueue.objects.create(
            title=title,
            video_id=video_id,
            thumbnail=thumbnail,
            channel=channel,
            audio_url=audio_url,
            artwork=artwork,
            requested_by=requested_by,
            client_id=client_id
        )"""
assert t.count(old1) == 1, "count=%d" % t.count(old1)
t = t.replace(old1, new1)
print("Fix1 ok")

old2 = """        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
        audio_url = str(data.get('audio_url', '')).strip()[:1000]
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
                requested_by=requested_by,
                client_id=client_id,
                created_at=first_song.created_at - timedelta(seconds=1)
            )"""
new2 = """        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
        audio_url = str(data.get('audio_url', '')).strip()[:1000]
        artwork = str(data.get('artwork', '')).strip()[:500]
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

old3 = """def get_queue(request):
    songs = SongQueue.objects.filter(is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by', 'audio_url'
    )
    return JsonResponse({'queue': list(songs)})"""
new3 = """def get_queue(request):
    songs = SongQueue.objects.filter(is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by', 'audio_url', 'artwork'
    )
    return JsonResponse({'queue': list(songs)})"""
assert t.count(old3) == 1, "count=%d" % t.count(old3)
t = t.replace(old3, new3)
print("Fix3 ok")

p.write_text(t, encoding="utf-8")
print("ALL FIXES APPLIED")
