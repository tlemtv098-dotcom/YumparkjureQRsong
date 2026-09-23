from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views
from . import views_auth

urlpatterns = [
    # Auth
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=views.ThaiLoginForm), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="/accounts/login/"), name="logout"),
    path("accounts/register/", views_auth.register_view, name="register"),
    path("accounts/profile/", views_auth.profile_view, name="profile"),
    path("accounts/password/", views_auth.change_password_view, name="change_password"),

    # Main pages
    path("", views.player_view, name="player"),
    path("embed-test/", views.embed_test, name="embed_test"),
    path("request/", views.request_view, name="request_view"),
    path("dashboard/", views_auth.dashboard_view, name="dashboard"),

    # API - Search & Hits
    path("api/search/", views.search_song, name="search_song"),
    path("api/hits/", views.hits, name="hits"),
    path("api/suggest/", views.suggest_song, name="suggest_song"),

    # API - Queue
    path("api/add/", views.add_to_queue, name="add_to_queue"),
    path("api/add-front/", views.add_to_queue_front, name="add_to_queue_front"),
    path("api/queue/", views.get_queue, name="get_queue"),
    path("api/queue/move/", views.move_queue, name="move_queue"),
    path("api/played/<int:song_id>/", views.mark_played, name="mark_played"),
    path("api/clear/", views.clear_queue, name="clear_queue"),

    # API - My Songs
    path("api/my-songs/", views.my_songs, name="my_songs"),
    path("api/my-songs/<int:song_id>/delete/", views.remove_my_song, name="remove_my_song"),

    # API - Playlists
    path("api/playlists/", views.playlist_list, name="playlist_list"),
    path("api/playlists/create/", views.playlist_create, name="playlist_create"),
    path("api/playlists/<int:pk>/", views.playlist_detail, name="playlist_detail"),
    path("api/playlists/<int:pk>/load/", views.playlist_load, name="playlist_load"),
    path("api/playlists/<int:pk>/add-song/", views.playlist_add_song, name="playlist_add_song"),

    # API - Admin/Stats
    path("api/block/clear/", views.clear_blocked, name="clear_blocked"),
    path("api/block/<str:video_id>/", views.block_video, name="block_video"),
    path("api/unblock/<str:video_id>/", views.unblock_video, name="unblock_video"),
    path("api/ai/recommend/", views.ai_recommend, name="ai_recommend"),
    path("api/clientlog/", views.client_log, name="client_log"),
    path("api/clientlog/recent/", views.client_log_recent, name="client_log_recent"),
    path("api/duration/", views.video_duration, name="video_duration"),
    path("api/audio/", views.audio_stream, name="audio_stream"),
    path("api/stats/", views.stats, name="stats"),

    # Export (Bonus)
    path("export/playlists/csv/", views_auth.export_playlists_csv, name="export_playlists_csv"),
    path("export/queue/csv/", views_auth.export_queue_csv, name="export_queue_csv"),

    # Management - User Management (changed from admin/ to management/)
    path("management/users/", views_auth.user_list_view, name="user_list"),
    path("management/users/create/", views_auth.user_create_view, name="user_create"),
    path("management/users/<int:pk>/edit/", views_auth.user_edit_view, name="user_edit"),
    path("management/users/<int:pk>/toggle/", views_auth.user_toggle_active_view, name="user_toggle_active"),
    path("management/users/<int:pk>/delete/", views_auth.user_delete_view, name="user_delete"),

    # Management - Genre Management
    path("management/genres/", views_auth.genre_list_view, name="genre_list"),
    path("management/genres/create/", views_auth.genre_create_view, name="genre_create"),
    path("management/genres/<int:pk>/edit/", views_auth.genre_edit_view, name="genre_edit"),
    path("management/genres/<int:pk>/delete/", views_auth.genre_delete_view, name="genre_delete"),

    # Management - Tag Management
    path("management/tags/", views_auth.tag_list_view, name="tag_list"),
    path("management/tags/create/", views_auth.tag_create_view, name="tag_create"),
    path("management/tags/<int:pk>/edit/", views_auth.tag_edit_view, name="tag_edit"),
    path("management/tags/<int:pk>/delete/", views_auth.tag_delete_view, name="tag_delete"),

    # Other
    path("qr.png", views.generate_qr, name="qr_code"),
    path("healthz/", views.healthz, name="healthz"),
    path("embed-test/", views.embed_test, name="embed_test"),
    re_path(r"^static/music/sw\.[0-9a-f]+\.js$", views.sw_compat, name="sw_compat"),
]
