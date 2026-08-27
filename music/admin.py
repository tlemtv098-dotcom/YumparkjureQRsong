from django.contrib import admin
from .models import SongQueue, BlockedVideo

@admin.register(BlockedVideo)
class BlockedVideoAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'reason', 'created_at')
    search_fields = ('video_id',)
    readonly_fields = ('created_at',)

@admin.register(SongQueue)
class SongQueueAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'requested_by', 'client_id', 'is_played', 'created_at')
    list_filter = ('is_played', 'channel', 'created_at')
    search_fields = ('title', 'channel', 'requested_by', 'client_id')
    list_per_page = 50
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
