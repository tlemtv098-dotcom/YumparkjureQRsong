import pathlib
p = pathlib.Path(r"D:\mysong\music\views_auth.py")
t = p.read_text(encoding="utf-8")

old = """@role_required(["admin"])
def export_playlists_csv(request):"""

new = """@login_required
def dashboard_stats_api(request):
    # API endpoint for dashboard charts data
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    period = int(request.GET.get("period", 7))
    if period not in [7, 30]:
        period = 7
    
    daily_stats = []
    for i in range(period):
        day = timezone.now().date() - timedelta(days=i)
        count = SongQueue.objects.filter(created_at__date=day).count()
        daily_stats.append({"date": day.strftime("%d/%m"), "count": count})
    daily_stats.reverse()
    
    top_songs = SongQueue.objects.filter(is_played=True).values("title", "video_id").annotate(
        play_count=Count("id")
    ).order_by("-play_count")[:10]
    
    status_stats = [
        {"status": "รอเล่น", "count": SongQueue.objects.filter(is_played=False).count()},
        {"status": "เล่นแล้ว", "count": SongQueue.objects.filter(is_played=True).count()},
        {"status": "คิวหน้า", "count": SongQueue.objects.filter(is_played=False).order_by("created_at")[:5].count()},
        {"status": "เล่นแล้ววันนี้", "count": SongQueue.objects.filter(is_played=True, created_at__date=timezone.now().date()).count()},
    ]
    
    return JsonResponse({
        "daily_stats": daily_stats,
        "top_songs": list(top_songs),
        "status_stats": status_stats,
    })


@role_required(["admin"])
def export_playlists_csv(request):"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Dashboard stats API added")
