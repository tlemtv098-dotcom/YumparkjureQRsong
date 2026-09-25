import pathlib
p = pathlib.Path(r"D:\mysong\music\views.py")
t = p.read_text(encoding="utf-8")

# Add pagination to playlist_list API
old = """@login_required
def playlist_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    playlists = Playlist.objects.filter(user=request.user)
    data = [{'id': p.id, 'name': p.name, 'songs': p.songs, 'created_at': p.created_at.isoformat()} for p in playlists]
    return JsonResponse({'playlists': data})"""

new = """@login_required
def playlist_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    playlists = Playlist.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    paginator = Paginator(playlists, per_page)
    page_obj = paginator.get_page(page)
    
    data = [{
        'id': p.id, 
        'name': p.name, 
        'description': p.description,
        'songs': p.songs, 
        'is_public': p.is_public,
        'genres': [g.name for g in p.genres.all()],
        'tags': [t.name for t in p.tags.all()],
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in page_obj.object_list]
    
    return JsonResponse({
        'playlists': data,
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
print("playlist_list pagination added")
