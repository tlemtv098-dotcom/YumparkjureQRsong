import io
import os
import re
import json
import random
import socket
import qrcode
import urllib.parse
import urllib.request
import urllib.error
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

ALBUM_RE = re.compile(r'longplay|รวม.*เพลง|ชั่วโมง|อัลบั้ม|60 minutes|playlist|ยาวๆ|ต่อเนื่อง|อันดับ|ชาร์ต|chart|billboard|Top 20|Compilation|Collection', re.I)
CHART_RE = re.compile(r'chart|อันดับ|ชาร์ต|Top 20|Billboard', re.I)
AI_RE = re.compile(r'\bAI\b|AurAIa|Artificial|Bot', re.I)
NON_MUSIC_RE = re.compile(r'สอน|how to|vlog|game|gameplay|compilation|collection', re.I)
def _is_album_title(title):
    return bool(ALBUM_RE.search(title or '') or _is_chart_title(title))
def _is_chart_title(title):
    return bool(CHART_RE.search(title or ''))
def _is_chart(title):
    return _is_chart_title(title)
def _is_ai_title(title, channel):
    return bool(AI_RE.search(title or '') or AI_RE.search(channel or ''))
def _is_non_music(title, channel):
    return bool(NON_MUSIC_RE.search(title or '') or NON_MUSIC_RE.search(channel or ''))
def _is_music_result(title, channel):
    return not _is_non_music(title, channel)

def _is_embeddable(video_id):
    try:
        opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, 'socket_timeout': 3}
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


def _youtube_api_keys():
    """Return ordered unique non-empty API keys from env (never log values)."""
    keys = []
    for part in (os.environ.get('YOUTUBE_API_KEYS') or '').split(','):
        candidate = part.strip()
        if candidate and candidate not in keys:
            keys.append(candidate)
    for env_name in ('YOUTUBE_API_KEY', 'key', 'YOUTUBE_API_KEY_2'):
        candidate = (os.environ.get(env_name) or '').strip()
        if candidate and candidate not in keys:
            keys.append(candidate)
    return keys


def youtube_api_search(query, max_results=8):
    """Search YouTube through the official API when a key is configured."""
    # Accept YOUTUBE_API_KEYS (comma-separated) plus the single-key names
    # currently used in local .env files / hosting env.
    api_keys = _youtube_api_keys()
    if not api_keys:
        return []

    for index, api_key in enumerate(api_keys, start=1):
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
                timeout=8,
            ) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode('utf-8', errors='ignore')
            except Exception:
                body = ''
            lowered = body.lower()
            if exc.code == 403 and ('quotaexceeded' in lowered or 'ratelimitexceeded' in lowered or 'quota' in lowered):
                print(f'YouTube API key {index} quota exceeded, trying next')
                continue
            print('YouTube API Error:', exc)
            return []
        except Exception as exc:
            print(f'YouTube API key {index} network error: {exc}, trying next')
            continue

        results = []
        for item in payload.get('items', []):
            video_id = item.get('id', {}).get('videoId')
            snippet = item.get('snippet', {})
            if not video_id or not re.match(r'^[A-Za-z0-9_-]{11}$', video_id) or _is_blocked(video_id):
                continue
            title = snippet.get('title', 'Unknown Title')
            if _is_album_title(title):
                continue
            channel = snippet.get('channelTitle', 'YouTube')
            if _is_ai_title(title, channel):
                continue
            if _is_non_music(title, channel):
                continue
            thumbnails = snippet.get('thumbnails', {})
            thumbnail = (thumbnails.get('medium') or thumbnails.get('default') or {}).get('url')
            results.append({
                'id': video_id,
                'title': title,
                'channel': channel,
                'thumbnail': thumbnail or f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
            })
        return results
    return []


def search_youtube(query, max_results=8):
    """Use the official API first; fast-fail to [] so search_song can fallback immediately."""
    api_results = youtube_api_search(query, max_results)
    if api_results:
        # API already filters videoEmbeddable=true + server-side title checks — return directly for speed.
        return api_results[:max_results]

    # Fast path: API empty (no key/quota/error) -> return [] immediately.
    # Do NOT call yt-dlp ytsearch or _is_embeddable in search path (slow, Render 429/bot).
    # YoutubeDL/_is_embeddable helpers kept for hits-only deep checks.
    return []

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
            {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/ks7p6DA0dKk/hqdefault.jpg"},
            {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/zwvv71slEYc/hqdefault.jpg"},
            {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://i.ytimg.com/vi/L1k0wkQ6uww/hqdefault.jpg"},
            {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/s-MZid-59Hc/hqdefault.jpg"},
            {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://i.ytimg.com/vi/rc7KnQAh_1I/hqdefault.jpg"},
        ]
        # simple filter by query substring
        q_lower = query.lower()
        results = [s for s in fallback if q_lower in s['title'].lower() or q_lower in s['channel'].lower()]
        if not results:
            results = fallback[:3]
        # filter blocked and album titles + non-music
        results = [r for r in results if not _is_blocked(r['id']) and not _is_album_title(r.get('title','')) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel',''))]
        if not results:
            # Guarantee non-empty: album/ai/non-music filters must not silently empty fallback.
            results = [r for r in fallback[:3] if not _is_blocked(r['id'])]
    else:
        # also filter live results (defense in depth) for album titles + non-music
        results = [r for r in results if not _is_album_title(r.get('title','')) and not _is_blocked(r['id']) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel',''))]
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
    # pick 2 random queries to broaden pool and return 10 unique (+fallback pad to 15) for speed
    k = min(2, len(queries))
    picked = random.sample(queries, k) if k else []
    # cache key versioned to avoid stale single-query cache; keep 60s but shuffle on hit
    cache_key = f"hits:{genre}:v3"
    try:
        cached = cache.get(cache_key)
    except Exception as e:
        print(f'hits cache.get failed: {e}')
        cached = None
    if cached:
        # ensure cached results also filtered (defense in depth) + non-music
        try:
            filtered_cached = [r for r in cached if not _is_blocked(r['id']) and not _is_album_title(r.get('title','')) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel',''))]
        except Exception as e:
            print(f'hits cached filter failed: {e}')
            filtered_cached = list(cached)
        # dedup cached as second layer
        seen_c = set()
        dedup_c = []
        for r in filtered_cached:
            if r['id'] not in seen_c:
                dedup_c.append(r); seen_c.add(r['id'])
        # shuffle a copy to avoid same order on refresh within 60s
        out_cached = list(dedup_c)
        random.shuffle(out_cached)
        return JsonResponse({'results': out_cached[:15]})
    # merge results from 2 queries (10 total, 5 per query)
    merged = []
    for q in picked:
        try:
            chunk = search_youtube(q, 5)
        except Exception:
            chunk = []
        if chunk:
            merged.extend(chunk)
    _fallback_static = [
        {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/ks7p6DA0dKk/hqdefault.jpg"},
        {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/zwvv71slEYc/hqdefault.jpg"},
        {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://i.ytimg.com/vi/L1k0wkQ6uww/hqdefault.jpg"},
        {"id": "yEbv0QiI1Ns", "title": "คนไม่สำคัญ - Safeplanet", "channel": "GMM", "thumbnail": "https://i.ytimg.com/vi/yEbv0QiI1Ns/hqdefault.jpg"},
        {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/s-MZid-59Hc/hqdefault.jpg"},
        {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://i.ytimg.com/vi/rc7KnQAh_1I/hqdefault.jpg"},
        {"id": "I9ZIq7ynvdU", "title": "แค่คนโทรผิด - Klear", "channel": "GMM", "thumbnail": "https://i.ytimg.com/vi/I9ZIq7ynvdU/hqdefault.jpg"},
        {"id": "Bk4O_3WF8II", "title": "ซ่อน(ไม่)หา - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/Bk4O_3WF8II/hqdefault.jpg"},
    ]
    try:
        if not merged:
            # Fallback static hits for PythonAnywhere free (YouTube blocked) - shuffle and dedup
            results = [r for r in _fallback_static if not _is_blocked(r['id']) and not _is_album_title(r.get('title','')) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel',''))]
        else:
            # also ensure live search results are filtered (defense in depth) + non-music
            results = [r for r in merged if not _is_blocked(r['id']) and not _is_album_title(r.get('title','')) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel',''))]
        # dedup via seen set + shuffle
        seen = set()
        dedup = []
        for r in results:
            if r['id'] not in seen and not _is_album_title(r.get('title','')) and not _is_blocked(r['id']) and not _is_ai_title(r.get('title',''), r.get('channel','')) and not _is_non_music(r.get('title',''), r.get('channel','')):
                dedup.append(r); seen.add(r['id'])
        # if live results deduped to less than 15, pad with fallback to ensure 15 non-duplicate
        if len(dedup) < 15:
            for fb in _fallback_static:
                if fb['id'] not in seen and not _is_blocked(fb['id']) and not _is_album_title(fb.get('title','')) and not _is_ai_title(fb.get('title',''), fb.get('channel','')) and not _is_non_music(fb.get('title',''), fb.get('channel','')):
                    dedup.append(fb); seen.add(fb['id'])
                if len(dedup) >= 15:
                    break
        random.shuffle(dedup)
        out = dedup[:15]
        try:
            cache.set(cache_key, out, 60)
        except Exception as e:
            print(f'hits cache.set failed: {e}')
        return JsonResponse({'results': out})
    except Exception as e:
        print(f'hits failed, returning static fallback: {e}')
        safe = [r for r in _fallback_static if r['id'] not in BLOCKED_VIDEO_IDS and not _is_album_title(r.get('title', '')) and not _is_ai_title(r.get('title', ''), r.get('channel', '')) and not _is_non_music(r.get('title', ''), r.get('channel', ''))]
        random.shuffle(safe)
        return JsonResponse({'results': safe[:15]})

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
        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
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
        thumbnail = str(data.get('thumbnail', f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg')).strip()[:500]
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

@csrf_exempt
def ai_recommend(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        data = {}
    mood = str(data.get("mood") or "").strip()
    if not mood:
        mood = "ทั่วไป"

    titles = []
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if api_key:
        try:
            prompt = f"แนะนำเพลงไทย 5 เพลงสำหรับอารมณ์ {mood} ตอบเป็น JSON list ของชื่อเพลง"
            payload = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            # Extract JSON array from content (handle markdown code blocks)
            m = re.search(r"\[.*\]", content, re.S)
            json_str = m.group(0) if m else content
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                titles = [str(t).strip() for t in parsed if str(t).strip()]
            elif isinstance(parsed, dict) and "songs" in parsed:
                titles = [str(t).strip() for t in parsed["songs"] if str(t).strip()]
        except Exception as e:
            print(f"ai_recommend DeepSeek error: {e}")
            titles = []

    songs = []
    for title in titles[:5]:
        try:
            res = search_youtube(title, 1)
            if res:
                songs.append(res[0])
        except Exception as e:
            print(f"ai_recommend search error for {title}: {e}")
            continue

    if len(songs) < 5:
        _fallback_static = [
            {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/ks7p6DA0dKk/hqdefault.jpg"},
            {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/zwvv71slEYc/hqdefault.jpg"},
            {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://i.ytimg.com/vi/L1k0wkQ6uww/hqdefault.jpg"},
            {"id": "yEbv0QiI1Ns", "title": "คนไม่สำคัญ - Safeplanet", "channel": "GMM", "thumbnail": "https://i.ytimg.com/vi/yEbv0QiI1Ns/hqdefault.jpg"},
            {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/s-MZid-59Hc/hqdefault.jpg"},
            {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://i.ytimg.com/vi/rc7KnQAh_1I/hqdefault.jpg"},
            {"id": "I9ZIq7ynvdU", "title": "แค่คนโทรผิด - Klear", "channel": "GMM", "thumbnail": "https://i.ytimg.com/vi/I9ZIq7ynvdU/hqdefault.jpg"},
            {"id": "Bk4O_3WF8II", "title": "ซ่อน(ไม่)หา - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/Bk4O_3WF8II/hqdefault.jpg"},
        ]
        try:
            fb_filtered = [r for r in _fallback_static if not _is_blocked(r["id"]) and not _is_album_title(r.get("title", "")) and not _is_ai_title(r.get("title", ""), r.get("channel", "")) and not _is_non_music(r.get("title", ""), r.get("channel", ""))]
        except Exception:
            fb_filtered = [r for r in _fallback_static if r["id"] not in BLOCKED_VIDEO_IDS and not _is_album_title(r.get("title", "")) and not _is_ai_title(r.get("title", ""), r.get("channel", "")) and not _is_non_music(r.get("title", ""), r.get("channel", ""))]
        random.shuffle(fb_filtered)
        existing_ids = {s.get("id") for s in songs}
        for r in fb_filtered:
            if r["id"] not in existing_ids:
                songs.append(r)
                existing_ids.add(r["id"])
            if len(songs) >= 5:
                break
        # If still less than 5 (e.g. heavy filtering), pad by reusing fallback
        idx = 0
        while len(songs) < 5 and fb_filtered:
            songs.append(fb_filtered[idx % len(fb_filtered)])
            idx += 1

    songs = songs[:5]
    # Final guarantee: if still empty, return static
    if len(songs) < 5:
        try:
            _static_fallback = _fallback_static  # type: ignore
        except NameError:
            _static_fallback = [
                {"id": "ks7p6DA0dKk", "title": "ข้างกัน - Three Man Down", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/ks7p6DA0dKk/hqdefault.jpg"},
                {"id": "zwvv71slEYc", "title": "ถ้าเธอ - Tilly Birds", "channel": "GeneLab", "thumbnail": "https://i.ytimg.com/vi/zwvv71slEYc/hqdefault.jpg"},
                {"id": "L1k0wkQ6uww", "title": "แฟนเก่าคนโปรด - SLAPKISS", "channel": "SLAPKISS", "thumbnail": "https://i.ytimg.com/vi/L1k0wkQ6uww/hqdefault.jpg"},
                {"id": "s-MZid-59Hc", "title": "แค่เธอ - Jeff Satur", "channel": "Jeff Satur", "thumbnail": "https://i.ytimg.com/vi/s-MZid-59Hc/hqdefault.jpg"},
                {"id": "rc7KnQAh_1I", "title": "รักแรกพบ - Tattoo Colour", "channel": "Tattoo Colour", "thumbnail": "https://i.ytimg.com/vi/rc7KnQAh_1I/hqdefault.jpg"},
            ]
        # Fill remaining slots from fallback
        existing = {s.get("id") for s in songs}
        for r in _static_fallback:
            if len(songs) >= 5:
                break
            if r["id"] not in existing:
                songs.append(r)
        songs = songs[:5]
    return JsonResponse({"songs": songs[:5]})


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
