# Generated migration to add database indexes for performance optimization
# Generated on 2025-01-15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0011_alter_genre_slug_alter_tag_slug'),
    ]

    operations = [
        # SongQueue indexes - Critical for queue queries
        migrations.AddIndex(
            model_name='songqueue',
            index=models.Index(fields=['is_played', 'created_at'], name='songqueue_played_created_idx'),
        ),
        migrations.AddIndex(
            model_name='songqueue',
            index=models.Index(fields=['video_id'], name='songqueue_video_id_idx'),
        ),
        migrations.AddIndex(
            model_name='songqueue',
            index=models.Index(fields=['requested_by'], name='songqueue_requested_by_idx'),
        ),
        migrations.AddIndex(
            model_name='songqueue',
            index=models.Index(fields=['-created_at'], name='songqueue_created_desc_idx'),
        ),

        # Playlist indexes
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['user', 'name'], name='playlist_user_name_idx'),
        ),
        migrations.AddIndex(
            model_name='playlist',
            index=models.Index(fields=['created_at'], name='playlist_created_idx'),
        ),

        # PlaylistSong indexes
        migrations.AddIndex(
            model_name='playlistsong',
            index=models.Index(fields=['playlist', 'position'], name='playlistsong_playlist_pos_idx'),
        ),
        migrations.AddIndex(
            model_name='playlistsong',
            index=models.Index(fields=['song'], name='playlistsong_song_idx'),
        ),

        # BlockedVideo index
        migrations.AddIndex(
            model_name='blockedvideo',
            index=models.Index(fields=['video_id'], name='blockedvideo_video_id_idx'),
        ),

        # GoodVideo indexes
        migrations.AddIndex(
            model_name='goodvideo',
            index=models.Index(fields=['video_id'], name='goodvideo_video_id_idx'),
        ),
        migrations.AddIndex(
            model_name='goodvideo',
            index=models.Index(fields=['-plays'], name='goodvideo_plays_desc_idx'),
        ),

        # ClientLog indexes
        migrations.AddIndex(
            model_name='clientlog',
            index=models.Index(fields=['session', 'created_at'], name='clientlog_session_created_idx'),
        ),
        migrations.AddIndex(
            model_name='clientlog',
            index=models.Index(fields=['event', 'created_at'], name='clientlog_event_created_idx'),
        ),
    ]