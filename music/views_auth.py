
# ============================================================
# AUTH & USER MANAGEMENT VIEWS (Day 1)
# ============================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .forms import RegisterForm, ProfileForm, UserForm, ProfileRoleForm
from .models import Profile, Playlist, Genre, Tag, SongQueue, BlockedVideo, GoodVideo


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and hasattr(user, "profile") and user.profile.is_admin()


def is_staff_role(user):
    """Check if user is staff or admin"""
    return user.is_authenticated and hasattr(user, "profile") and user.profile.is_staff_role()


def role_required(allowed_roles):
    """Decorator for role-based access control"""
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, "profile"):
                messages.error(request, "ไม่พบโปรไฟล์ผู้ใช้")
                return redirect("player")
            if request.user.profile.role not in allowed_roles:
                messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
                return redirect("player")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def register_view(request):
    """User registration"""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile is created automatically via signal
            # Set default role to customer
            profile = user.profile
            profile.role = "customer"
            profile.phone = form.cleaned_data.get("phone", "")
            profile.save()
            login(request, user)
            messages.success(request, "สมัครสมาชิกสำเร็จ! ยินดีต้อนรับสู่ระบบ")
            return redirect("player")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile_view(request):
    """User profile view/edit"""
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตโปรไฟล์สำเร็จ")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "registration/profile.html", {"form": form, "profile": profile})


@login_required
def change_password_view(request):
    """Change password"""
    if request.method == "POST":
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "เปลี่ยนรหัสผ่านสำเร็จ")
            return redirect("profile")
    else:
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user)
    return render(request, "registration/change_password.html", {"form": form})


# ============================================================
# ADMIN USER MANAGEMENT
# ============================================================

@role_required(["admin"])
def user_list_view(request):
    """List all users with pagination and search"""
    query = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")

    users = User.objects.select_related("profile").all().order_by("-date_joined")

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if role_filter:
        users = users.filter(profile__role=role_filter)
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "admin/user_list.html", {
        "page_obj": page_obj,
        "query": query,
        "role_filter": role_filter,
        "status_filter": status_filter,
    })


@role_required(["admin"])
def user_create_view(request):
    """Create new user (admin only)"""
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = ProfileRoleForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(User.objects.make_random_password())
            user.save()
            profile = user.profile
            profile.role = profile_form.cleaned_data["role"]
            profile.save()
            messages.success(request, f"สร้างผู้ใช้ {user.username} สำเร็จ (รหัสผ่านสุ่มถูกสร้าง)")
            return redirect("user_list")
    else:
        user_form = UserForm()
        profile_form = ProfileRoleForm()
    return render(request, "admin/user_form.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "title": "เพิ่มผู้ใช้ใหม่",
    })


@role_required(["admin"])
def user_edit_view(request, pk):
    """Edit user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileRoleForm(request.POST, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"อัปเดตผู้ใช้ {user.username} สำเร็จ")
            return redirect("user_list")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileRoleForm(instance=user.profile)
    return render(request, "admin/user_form.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "title": f"แก้ไขผู้ใช้: {user.username}",
        "user_obj": user,
    })


@role_required(["admin"])
@require_http_methods(["POST"])
def user_toggle_active_view(request, pk):
    """Toggle user active status"""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        return JsonResponse({"success": False, "error": "ไม่สามารถปิดการใช้งานตัวเองได้"})
    user.is_active = not user.is_active
    user.save()
    return JsonResponse({"success": True, "is_active": user.is_active})


@role_required(["admin"])
@require_http_methods(["POST"])
def user_delete_view(request, pk):
    """Delete user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        return JsonResponse({"success": False, "error": "ไม่สามารถลบตัวเองได้"})
    username = user.username
    user.delete()
    return JsonResponse({"success": True, "message": f"ลบผู้ใช้ {username} สำเร็จ"})


# ============================================================
# GENRE & TAG MANAGEMENT (Admin/Staff)
# ============================================================

@role_required(["admin", "staff"])
def genre_list_view(request):
    """List genres with pagination"""
    query = request.GET.get("q", "")
    genres = Genre.objects.annotate(playlist_count=Count("playlists")).order_by("name")
    if query:
        genres = genres.filter(Q(name__icontains=query) | Q(description__icontains=query))
    paginator = Paginator(genres, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "admin/genre_list.html", {"page_obj": page_obj, "query": request.GET.get("q", "")})


@role_required(["admin", "staff"])
def genre_create_view(request):
    if request.method == "POST":
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มแนวเพลงสำเร็จ")
            return redirect("genre_list")
    else:
        form = GenreForm()
    return render(request, "admin/genre_form.html", {"form": form, "title": "เพิ่มแนวเพลง"})


@role_required(["admin", "staff"])
def genre_edit_view(request, pk):
    genre = get_object_or_404(Genre, pk=pk)
    if request.method == "POST":
        form = GenreForm(request.POST, instance=genre)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขแนวเพลงสำเร็จ")
            return redirect("genre_list")
    else:
        form = GenreForm(instance=genre)
    return render(request, "admin/genre_form.html", {"form": form, "title": f"แก้ไข: {genre.name}"})


@role_required(["admin", "staff"])
@require_http_methods(["POST"])
def genre_delete_view(request, pk):
    genre = get_object_or_404(Genre, pk=pk)
    genre.delete()
    return JsonResponse({"success": True})


@role_required(["admin", "staff"])
def tag_list_view(request):
    query = request.GET.get("q", "")
    tags = Tag.objects.annotate(playlist_count=Count("playlists")).order_by("name")
    if query:
        tags = tags.filter(name__icontains=query)
    paginator = Paginator(tags, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "admin/tag_list.html", {"page_obj": page_obj, "query": request.GET.get("q", "")})


@role_required(["admin", "staff"])
def tag_create_view(request):
    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มแท็กสำเร็จ")
            return redirect("tag_list")
    else:
        form = TagForm()
    return render(request, "admin/tag_form.html", {"form": form, "title": "เพิ่มแท็ก"})


@role_required(["admin", "staff"])
def tag_edit_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขแท็กสำเร็จ")
            return redirect("tag_list")
    else:
        form = TagForm(instance=tag)
    return render(request, "admin/tag_form.html", {"form": form, "title": f"แก้ไข: {tag.name}"})


@role_required(["admin", "staff"])
@require_http_methods(["POST"])
def tag_delete_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    tag.delete()
    return JsonResponse({"success": True})


# ============================================================
# DASHBOARD STATS (Bonus)
# ============================================================

@login_required
def dashboard_view(request):
    """Dashboard with stats and charts data"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta

    # Basic stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_playlists = Playlist.objects.count()
    total_queued = SongQueue.objects.filter(is_played=False).count()
    total_played = SongQueue.objects.filter(is_played=True).count()

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_queued = SongQueue.objects.filter(created_at__gte=week_ago).count()
    recent_users = User.objects.filter(date_joined__gte=week_ago).count()

    # Top genres
    top_genres = Genre.objects.annotate(
        song_count=Count("queued_songs")
    ).filter(song_count__gt=0).order_by("-song_count")[:5]

    # Daily queue stats (last 7 days)
    daily_stats = []
    for i in range(7):
        day = timezone.now().date() - timedelta(days=i)
        count = SongQueue.objects.filter(created_at__date=day).count()
        daily_stats.append({"date": day.strftime("%d/%m"), "count": count})
    daily_stats.reverse()

    # Top songs (by play count)
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
    return render(request, "dashboard.html", context)


@role_required(["admin"])
def export_playlists_csv(request):
    """Export playlists to CSV"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = "attachment; filename=playlists.csv"
    writer = csv.writer(response)
    writer.writerow(["ID", "User", "Name", "Description", "Public", "Songs Count", "Created"])
    for pl in Playlist.objects.select_related("user").all():
        writer.writerow([
            pl.id, pl.user.username, pl.name, pl.description,
            "Yes" if pl.is_public else "No", len(pl.songs), pl.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    return response


@role_required(["admin"])
def export_queue_csv(request):
    """Export queue to CSV"""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = "attachment; filename=queue.csv"
    writer = csv.writer(response)
    writer.writerow(["ID", "Title", "Video ID", "Channel", "Requested By", "Played", "Created"])
    for sq in SongQueue.objects.all().order_by("-created_at"):
        writer.writerow([
            sq.id, sq.title, sq.video_id, sq.channel, sq.requested_by,
            "Yes" if sq.is_played else "No", sq.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    return response
