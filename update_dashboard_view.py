import pathlib
p = pathlib.Path(r"D:\mysong\music\views_auth.py")
t = p.read_text(encoding="utf-8")

old = """    context = {
        "total_users": total_users,
        "active_users": active_users,
        "total_playlists": total_playlists,
        "total_queued": total_queued,
        "total_played": total_played,
        "recent_queued": recent_queued,
        "recent_users": recent_users,
        "top_genres": top_genres,
        "daily_stats": daily_stats,
    }
    return render(request, "dashboard.html", context)"""

new = """    # Top songs (by play count)
    top_songs = SongQueue.objects.filter(is_played=True).values("title", "video_id").annotate(
        play_count=Count("id")
    ).order_by("-play_count")[:10]

    # Status stats for doughnut chart
    status_stats = [
        {"status": "รอเล่น", "count": SongQueue.objects.filter(is_played=False).count()},
        {"status": "เล่นแล้ว", "count": SongQueue.objects.filter(is_played=True).count()},
        {"status": "คิวหน้า", "count": SongQueue.objects.filter(is_played=False).order_by("created_at")[:5].count()},
        {"status": "เล่นแล้ววันนี้", "count": SongQueue.objects.filter(is_played=True, created_at__date=timezone.now().date()).count()},
    ]

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "total_playlists": total_playlists,
        "total_queued": total_queued,
        "total_played": total_played,
        "recent_queued": recent_queued,
        "recent_users": recent_users,
        "top_genres": top_genres,
        "daily_stats": daily_stats,
        "top_songs": list(top_songs),
        "status_stats": status_stats,
    }
    return render(request, "dashboard.html", context)"""

assert t.count(old) == 1, "count=%d" % t.count(old)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("Dashboard view updated with top_songs and status_stats")
