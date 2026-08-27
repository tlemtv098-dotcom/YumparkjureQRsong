from django.urls import path
from . import views

urlpatterns = [
    path('', views.player_view, name='player'),
    path('request/', views.request_view, name='request_view'),
    path('api/search/', views.search_song, name='search_song'),
    path('api/hits/', views.hits, name='hits'),
    path('api/add/', views.add_to_queue, name='add_to_queue'),
    path('api/queue/', views.get_queue, name='get_queue'),
    path('api/played/<int:song_id>/', views.mark_played, name='mark_played'),
    path('api/clear/', views.clear_queue, name='clear_queue'),
    path('api/my-songs/', views.my_songs, name='my_songs'),
    path('api/my-songs/<int:song_id>/delete/', views.remove_my_song, name='remove_my_song'),
    path('qr.png', views.generate_qr, name='qr_code'),
    path('api/suggest/', views.suggest_song, name='suggest_song'),
    path('api/block/<str:video_id>/', views.block_video, name='block_video'),
    path('healthz/', views.healthz, name='healthz'),
    path('api/stats/', views.stats, name='stats'),
]
