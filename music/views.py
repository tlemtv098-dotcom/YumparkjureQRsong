import io
import os
import re
import json
import random
import socket
import qrcode
import urllib.parse
import urllib.request
import time
from collections import defaultdict
from datetime import timedelta
from yt_dlp import YoutubeDL
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.core.cache import cache
from django.db.models import Count
from .models import SongQueue, BlockedVideo

def _is_owner(request):
    return request.headers.get('X-Player-Token') == settings.PLAYER_TOKEN or (request.user.is_authenticated and request.user.is_staff)

# Video IDs with embedding disabled (Error 153) - filtered server-side
# Many Thai songs from GMM, etc. have embedding disabled
BLOCKED_VIDEO_IDS = {
    'jNQXAC9IVRw',
    'dQw4w9WgXcQ',
    'qguo-j5PxBE',
}
def _is_blocked(video_id):
    if video_id in BLOCKED_VIDEO_IDS:
        return True
    return BlockedVideo.objects.filter(video_id=video_id).exists()
def _get_blocked_ids():
    db_ids = set(BlockedVideo.objects.values_list('video_id', flat=True))
    return BLOCKED_VIDEO_IDS | db_ids

ALBUM_RE = re.compile(r'longplay|รวมเพลง|ชั่วโมง|อัลบั้ม|60 minutes|playlist|ยาวๆ|ต่อเนื่อง', re.I)
def _is_album_title(title):
    return bool(ALBUM_RE.search(title or ''))

def _is_embeddable(video_id):
    try:
        opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'socket_timeout': 5}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            if not info:
                return None  # network or unknown
            if info.get('playable_in_embed') is False:
                return False
            if info.get('availability') in ('private', 'premium_only', 'subscriber_only'):
                return False
            status = info.get('playabilityStatus', {})
            if isinstance(status, dict) and status.get('status') in ('ERROR', 'UNPLAYABLE'):
                reason = status.get('reason', '') or ''
                if 'embedding' in reason.lower() or 'blocked' in reason.lower():
                    return False
                return False
            return True
    except Exception as e:
        # Network block or yt-dlp error — don't conclude not embeddable
        print(f'_is_embeddable check failed for {video_id}: {e}')
        return None

_rate_limit_store = defaultdict(list)
def _check_rate_limit(request, limit=30, window=10):
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    now = time.time()
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < window]
    if len(_rate_limit_store[ip]) >= limit:
        return False
    _rate_limit_store[ip].append(now)
    return True


def youtube_api_search(query, max_results=8):
    """Search YouTube through the official API when a key is configured."""
    # Accept the correctly named variable and the temporary `key` name
    # currently used in some local .env files.
    api_key = (os.environ.get('YOUTUBE_API_KEY') or os.environ.get('key', '')).strip()
    if not api_key:
        return []

    params = urllib.parse.urlencode({
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': min(max_results, 50),
        'regionCode': 'TH',
        'videoCategoryId': '10',
        'videoEmbeddable': 'true',
        'videoSyndicated': 'true',
        'key': api_key,
    })
    try:
        with urllib.request.urlopen(
            f'https://www.googleapis.com/youtube/v3/search?{params}',
            timeout=15,
        ) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        print('YouTube API Error:', exc)
        return []

    results = []
    for item in payload.get('items', []):
        video_id = item.get('id', {}).get('videoId')
        snippet = item.get('snippet', {})
        if not video_id or _is_blocked(video_id):
            continue
        title = snippet.get('title', 'Unknown Title')
        if _is_album_title(title):
            continue
        thumbnails = snippet.get('thumbnails', {})
        thumbnail = (thumbnails.get('medium') or thumbnails.get('default') or {}).get('url')
        results.append({
            'id': video_id,
            'title': title,
            'channel': snippet.get('channelTitle', 'YouTube'),
            'thumbnail': thumbnail or f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg',
        })
    return results


def search_youtube(query, max_results=8):
    """Use the official API first, retaining yt-dlp as a local fallback."""
    api_results = youtube_api_search(query, max_results)
    if api_results:
        filtered = []
        for r in api_results[:max_results]:
            if _is_album_title(r.get('title', '')):
                continue
            cache_key = f"embed:{r['id']}"
            cached = cache.get(cache_key)
            if cached is True or cached is False:
                embed = cached
            else:
                embed = _is_embeddable(r['id'])
                if embed is not None:
                    cache.set(cache_key, embed, 3600)
                else:
                    cache.set(cache_key, True, 60)
            if embed is False:
                try:
                    BlockedVideo.objects.get_or_create(video_id=r['id'], defaults={'reason': 'Not embeddable'})
                except:
                    pass
                continue
            # embed is True or None (network) -> keep
            filtered.append(r)
            if len(filtered) >= max_results:
                break
        return filtered if filtered else []

    ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True, 'default_search': f'ytsearch{max_results}'}
    raw = []
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch{max_results}:{query}', download=False)
            for entry in info.get('entries', []):
                vid_id = entry.get('id')
                if not vid_id or _is_blocked(vid_id):
                    continue
                if _is_album_title(entry.get('title','')):
                    continue
                raw.append({'id': vid_id, 'title': entry.get('title','Unknown'), 'channel': entry.get('uploader') or entry.get('channel','YouTube'), 'thumbnail': f'https://img.youtube.com/vi/{vid_id}/mqdefault.jpg'})
        except Exception as e:
            print('Search Error:', e)
            return []
    # Now check embeddable per video (slow but accurate) — limit to first max_results to keep time <5s
    filtered = []
    for r in raw[:max_results]:
        if _is_album_title(r.get('title', '')):
            continue
        cache_key = f"embed:{r['id']}"
        cached = cache.get(cache_key)
        if cached is True or cached is False:
            embed = cached
        else:
            embed = _is_embeddable(r['id'])
            if embed is not None:
                cache.set(cache_key, embed, 3600)
            else:
                cache.set(cache_key, True, 60)
        if embed is True or embed is None:
            filtered.append(r)
        elif embed is False:
            try:
                BlockedVideo.objects.get_or_create(video_id=r['id'], defaults={'reason': 'Not embeddable'})
            except:
                pass
        if len(filtered) >= max_results:
            break
    return filtered[:max_results] if filtered else []

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@ensure_csrf_cookie
def player_view(request):
    local_ip = get_local_ip()
    request_url = f'http://{local_ip}:8000/request/'
    return render(request, 'music/player.html', {'request_url': request_url, 'PLAYER_TOKEN': settings.PLAYER_TOKEN})

@ensure_csrf_cookie
def request_view(request):
    return render(request, 'music/request.html')

def search_song(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    results = search_youtube(query, 5)
    if not results:
        # Fallback for PythonAnywhere free where yt-dlp blocked — return hits-style fallback filtered by query
        fallback = [
            {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://img.youtube.com/vi/ks7p6DA0dKk/mqdefault.jpg"},
            {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://img.youtube.com/vi/zwvv71slEYc/mqdefault.jpg"},
            {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://img.youtube.com/vi/L1k0wkQ6uww/mqdefault.jpg"},
            {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://img.youtube.com/vi/s-MZid-59Hc/mqdefault.jpg"},
            {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://img.youtube.com/vi/rc7KnQAh_1I/mqdefault.jpg"},
        ]
        # simple filter by query substring
        q_lower = query.lower()
        results = [s for s in fallback if q_lower in s['title'].lower() or q_lower in s['channel'].lower()]
        if not results:
            results = fallback[:3]
        # filter blocked and album titles
        results = [r for r in results if not _is_blocked(r['id']) and not _is_album_title(r.get('title',''))]
    else:
        # also filter live results (defense in depth) for album titles
        results = [r for r in results if not _is_album_title(r.get('title','')) and not _is_blocked(r['id'])]
    return JsonResponse({'results': results})

def suggest_song(request):
    query = request.GET.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    cache_key = f"suggest:{query}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'suggestions': cached})
    
    # Common Thai song/artist suggestions
    suggestions_pool = [
        "เพลงไทยฮิต", "เพลงรัก", "เพลงเศร้า", "เพลงแดนซ์", "เพลงอกหัก",
        "เพลงสนุก", "เพลงเพราะๆ", "เพลงใหม่", "เพลงเก่า",
        "Three Man Down", "Tilly Birds", "Polycat", "Scrubb", "Paradox",
        "Bodyslam", "Cocktail", "Slot Machine", "Potato", "Instinct",
        "Jeff Satur", "SLAPKISS", "Tattoo Colour", "Nont Tanont",
        "Palmy", "Bird Thongchai", "Ice Sarunyu", "Stamp Apiwat",
        "ลิปسودา", "getsunova", "Carnival", "Safeplanet", "Whal & Dolph",
        "Musketeers", "Klear", "Sweet Mullet", "Bodyslam",
        "Ying Likit", "Ter", "album", "cover", "live",
        "รักแรกพบ", "แค่เธอ", "ข้างกัน", "ถ้าเธอ", "คนไม่สำคัญ",
        "แฟนเก่าคนโปรด", "แค่คนโทรผิด", "ซ่อนไม่หา",
    ]
    
    results = [s for s in suggestions_pool if query in s.lower()]
    results = results[:8]
    cache.set(cache_key, results, 30)
    return JsonResponse({'suggestions': results})

def hits(request):
    genre = request.GET.get('genre', '').strip().lower()
    genre_queries = {
        'pop': ['เพลงป๊อปฮิต', 'เพลงป๊อป 2025'],
        'rock': ['เพลงร็อกฮิต', 'เพลงร็อกไทย'],
        'lukthung': ['เพลงลูกทุ่งฮิต', 'เพลงลูกทุ่ง 2025'],
        'tiktok': ['เพลงฮิต tiktok', 'เพลง tiktok 2025'],
        'old': ['เพลงเก่าฮิต 90', 'เพลงยุค 90'],
    }
    if genre in genre_queries:
        queries = genre_queries[genre]
    else:
        queries = ['เพลงไทยฮิต', 'เพลงฮิต 2025', 'เพลงดัง', 'เพลงใหม่ 2025', 'เพลงไทยเพราะๆ', 'เพลงฮิตติดชาร์ต']
    query = random.choice(queries)
    cache_key = f"hits:{genre}:{query}"
    cached = cache.get(cache_key)
    if cached:
        # ensure cached results also filtered (defense in depth)
        filtered_cached = [r for r in cached if not _is_blocked(r['id']) and not _is_album_title(r.get('title',''))]
        # dedup cached as second layer
        seen_c = set()
        dedup_c = []
        for r in filtered_cached:
            if r['id'] not in seen_c:
                dedup_c.append(r); seen_c.add(r['id'])
        return JsonResponse({'results': dedup_c[:10]})
    results = search_youtube(query, 10)
    if not results:
        # Fallback static hits for PythonAnywhere free (YouTube blocked)
        results = [
            {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://img.youtube.com/vi/ks7p6DA0dKk/mqdefault.jpg"},
            {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://img.youtube.com/vi/zwvv71slEYc/mqdefault.jpg"},
            {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://img.youtube.com/vi/L1k0wkQ6uww/mqdefault.jpg"},
            {"id": "yEbv0QiI1Ns", "title": "คนไม่สำคัญ - Safeplanet", "channel": "GMM", "thumbnail": "https://img.youtube.com/vi/yEbv0QiI1Ns/mqdefault.jpg"},
            {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://img.youtube.com/vi/s-MZid-59Hc/mqdefault.jpg"},
            {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://img.youtube.com/vi/rc7KnQAh_1I/mqdefault.jpg"},
            {"id": "I9ZIq7ynvdU", "title": "แค่คนโทรผิด - Klear", "channel": "GMM", "thumbnail": "https://img.youtube.com/vi/I9ZIq7ynvdU/mqdefault.jpg"},
            {"id": "o2NiIUFFd1M", "title": "ธาตุทองซาวด์ - YOUNGOHM", "channel": "YOUNGOHM", "thumbnail": "https://img.youtube.com/vi/o2NiIUFFd1M/mqdefault.jpg"},
            {"id": "VZoB0Vd9nQ", "title": "ซ่อนไม่หา - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://img.youtube.com/vi/VZoB0Vd9nQ/mqdefault.jpg"},
            {"id": "9bZkp7q19f0", "title": "ลืมไปแล้วว่ายังไง - Silly Fools", "channel": "GMM", "thumbnail": "https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg"},
        ]
        # filter blocked and album titles before return — never serve Error 153 to UI
        results = [r for r in results if not _is_blocked(r['id']) and not _is_album_title(r.get('title',''))]
    else:
        # also ensure live search results are filtered (defense in depth)
        results = [r for r in results if not _is_blocked(r['id']) and not _is_album_title(r.get('title',''))]
    # dedup + shuffle second layer (search_youtube already filters but hits adds defense)
    seen = set()
    dedup = []
    for r in results:
        if r['id'] not in seen and not _is_album_title(r.get('title','')) and not _is_blocked(r['id']):
            dedup.append(r); seen.add(r['id'])
    random.shuffle(dedup)
    out = dedup[:10]
    cache.set(cache_key, out, 60)
    return JsonResponse({'results': out})

def add_to_queue(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'error': 'Invalid JSON'}, status=400)
        
        # Validate required fields
        video_id = data.get('video_id')
        title_raw = str(data.get('title', '')).strip()
        if not video_id or not title_raw:
            return JsonResponse({'status': 'failed', 'error': 'กรุณาใส่ชื่อเพลง'}, status=400)
        
        if _is_album_title(title_raw):
            return JsonResponse({'status':'failed','error':'เพลงอัลบั้ม/รวมเพลงยาวเกินไป กรุณาเลือกเพลงเดี่ยว'}, status=400)

        # Check if video is blocked
        if _is_blocked(video_id):
            return JsonResponse({'status': 'failed', 'error': 'เพลงนี้เล่นไม่ได้ (ลิขสิทธิ์) ลองเลือกเพลงอื่นนะ'}, status=400)
        
        if not _check_rate_limit(request):
            return JsonResponse({'status': 'failed', 'error': 'ส่งคำขอเร็วเกินไป รอสักครู่'}, status=429)
        # Dedup: same video_id already in queue
        if SongQueue.objects.filter(video_id=video_id, is_played=False).exists():
            return JsonResponse({'status': 'failed', 'error': 'เพลงนี้อยู่ในคิวแล้ว'}, status=400)
        # Limit per client (max 5 queued per client_id)
        client_id = data.get('client_id', '')
        if client_id:
            if SongQueue.objects.filter(client_id=client_id, is_played=False).count() >= 5:
                return JsonResponse({'status': 'failed', 'error': 'คุณมีเพลงในคิวครบ 5 เพลงแล้ว รอให้เล่นก่อนนะ'}, status=400)
        # Also sanitize title length
        title = data.get('title', 'Unknown Title')[:255]
        title = title.strip()[:255]
        channel = str(data.get('channel', 'YouTube')).strip()[:255]
        requested_by = str(data.get('requested_by', 'ลูกค้าในร้าน')).strip()[:100]
        thumbnail = str(data.get('thumbnail', f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg')).strip()[:500]
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
        )
        return JsonResponse({'status': 'success', 'song_id': song.id})
    return JsonResponse({'status': 'failed', 'error': 'Method not allowed'}, status=405)


def add_to_queue_front(request):
    """Add song to FRONT of queue (priority play for owner)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'error': 'Invalid JSON'}, status=400)
        
        video_id = data.get('video_id')
        title_raw = str(data.get('title', '')).strip()
        if not video_id or not title_raw:
            return JsonResponse({'status': 'failed', 'error': 'กรุณาใส่ชื่อเพลง'}, status=400)
        
        if _is_album_title(title_raw):
            return JsonResponse({'status':'failed','error':'เพลงอัลบั้ม/รวมเพลงยาวเกินไป กรุณาเลือกเพลงเดี่ยว'}, status=400)

        if _is_blocked(video_id):
            return JsonResponse({'status': 'failed', 'error': 'เพลงนี้เล่นไม่ได้ (ลิขสิทธิ์) ลองเลือกเพลงอื่นนะ'}, status=400)
        
        if not _check_rate_limit(request):
            return JsonResponse({'status': 'failed', 'error': 'ส่งคำขอเร็วเกินไป รอสักครู่'}, status=429)
        
        # Dedup: same video_id already in queue
        if SongQueue.objects.filter(video_id=video_id, is_played=False).exists():
            return JsonResponse({'status': 'failed', 'error': 'เพลงนี้อยู่ในคิวแล้ว'}, status=400)
        
        # Limit per client (max 5 queued per client_id) - manual uses special client_id
        client_id = data.get('client_id', '')
        if client_id and client_id.startswith('manual_'):
            # Manual play has no limit
            pass
        elif client_id:
            if SongQueue.objects.filter(client_id=client_id, is_played=False).count() >= 5:
                return JsonResponse({'status': 'failed', 'error': 'คุณมีเพลงในคิวครบ 5 เพลงแล้ว รอให้เล่นก่อนนะ'}, status=400)
        
        title = title_raw[:255]
        channel = str(data.get('channel', 'YouTube')).strip()[:255]
        requested_by = str(data.get('requested_by', 'เจ้าของร้าน (เล่นเอง - ข้ามคิว)')).strip()[:100]
        thumbnail = str(data.get('thumbnail', f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg')).strip()[:500]
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
            )
        else:
            # Queue empty, normal create
            new_song = SongQueue.objects.create(
                title=title,
                video_id=video_id,
                thumbnail=thumbnail,
                channel=channel,
                audio_url=audio_url,
                requested_by=requested_by,
                client_id=client_id
            )
        
        return JsonResponse({'status': 'success', 'song_id': new_song.id, 'priority': True})
    return JsonResponse({'status': 'failed', 'error': 'Method not allowed'}, status=405)

def get_queue(request):
    songs = SongQueue.objects.filter(is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by', 'audio_url'
    )
    return JsonResponse({'queue': list(songs)})

@csrf_exempt
def mark_played(request, song_id):
    if not _is_owner(request):
        return JsonResponse({'error':'forbidden'}, status=403)
    SongQueue.objects.filter(id=song_id).update(is_played=True)
    return JsonResponse({'status': 'updated'})

@csrf_exempt
def move_queue(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    if not _is_owner(request):
        return JsonResponse({'error': 'forbidden'}, status=403)
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'invalid'}, status=400)
    song_id = data.get('song_id')
    position = data.get('position')
    if not song_id:
        return JsonResponse({'error': 'missing song_id'}, status=400)
    try:
        song = SongQueue.objects.get(id=song_id, is_played=False)
    except SongQueue.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)
    first = SongQueue.objects.filter(is_played=False).order_by('created_at').first()
    if not first or song.id == first.id:
        return JsonResponse({'status': 'success'})
    # For MVP: move to next/top by placing before first
    if position in ('next', 'top', None):
        song.created_at = first.created_at - timedelta(seconds=1)
        song.save()
        return JsonResponse({'status': 'success'})
    song.created_at = first.created_at - timedelta(seconds=1)
    song.save()
    return JsonResponse({'status': 'success'})


def clear_queue(request):
    if not _is_owner(request):
        return JsonResponse({'error':'forbidden'}, status=403)
    SongQueue.objects.all().delete()
    return JsonResponse({'status': 'cleared'})

def my_songs(request):
    client_id = request.GET.get('client_id', '')
    songs = SongQueue.objects.filter(client_id=client_id, is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'audio_url'
    )
    return JsonResponse({'songs': list(songs)})

def remove_my_song(request, song_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        client_id = data.get('client_id', '')
        deleted = SongQueue.objects.filter(id=song_id, client_id=client_id).delete()[0]
        return JsonResponse({'status': 'deleted' if deleted else 'not_found'})
    return JsonResponse({'status': 'failed'}, status=400)

def block_video(request, video_id):
    if request.method == 'POST':
        BlockedVideo.objects.get_or_create(video_id=video_id, defaults={'reason': 'Error 153'})
        return JsonResponse({'status': 'blocked', 'video_id': video_id})
    return JsonResponse({'status': 'failed'}, status=405)

def healthz(request):
    return JsonResponse({"status": "ok"})

def stats(request):
    total_queued = SongQueue.objects.filter(is_played=False).count()
    total_played = SongQueue.objects.filter(is_played=True).count()
    top = list(SongQueue.objects.values('video_id', 'title', 'channel').annotate(count=Count('id')).order_by('-count')[:5])
    return JsonResponse({"total_queued": total_queued, "total_played": total_played, "top_songs": top})

def generate_qr(request):
    # Use public URL from env var, fallback to request host
    public_url = os.environ.get('PUBLIC_URL')
    if public_url:
        qr_url = f'{public_url.rstrip("/")}/request/'
    else:
        # Build from request host (works on Railway with proper host header)
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        # Validate host format
        if not host or ' ' in host:
            host = 'web-production-2c2ef.up.railway.app'
        qr_url = f'{scheme}://{host}/request/'
    
    try:
        qr_img = qrcode.make(qr_url)
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except Exception as e:
        # Fallback QR code
        fallback_url = 'https://web-production-2c2ef.up.railway.app/request/'
        qr_img = qrcode.make(fallback_url)
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        return HttpResponse(buffer.getvalue(), content_type='image/png')
