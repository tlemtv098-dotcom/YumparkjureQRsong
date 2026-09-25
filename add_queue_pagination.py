import pathlib
p = pathlib.Path(r"D:\mysong\music\views.py")
t = p.read_text(encoding="utf-8")

old = """def get_queue(request):
    songs = SongQueue.objects.filter(is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by', 'audio_url', 'artwork'
    )
    return JsonResponse({'queue': list(songs)})"""

new = """def get_queue(request):
    # Pagination support
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    
    songs_qs = SongQueue.objects.filter(is_played=False).order_by('created_at')
    paginator = Paginator(songs_qs, per_page)
    page_obj = paginator.get_page(page)
    
    songs = page_obj.object_list.values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by', 'audio_url', 'artwork'
    )
    return JsonResponse({
        'queue': list(songs),
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'per_page': per_page
        }
    })"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("get_queue pagination added")
