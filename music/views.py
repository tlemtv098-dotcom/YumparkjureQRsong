import io
import json
import random
import socket
import qrcode
from yt_dlp import YoutubeDL
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SongQueue

# Video IDs with embedding disabled (Error 153) - filtered server-side
BLOCKED_VIDEO_IDS = {
    'jNQXAC9IVRw',  # Me at the zoo
    'dQw4w9WgXcQ',  # Never Gonna Give You Up
    'qguo-j5PxBE',  # ซ่อน(ไม่)หา - Jeff Satur
}

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

def player_view(request):
    local_ip = get_local_ip()
    request_url = f'http://{local_ip}:8000/request/'
    return render(request, 'music/player.html', {'request_url': request_url})

def request_view(request):
    return render(request, 'music/request.html')

def search_song(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'default_search': 'ytsearch5'
    }
    
    results = []
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch5:{query}', download=False)
            for entry in info.get('entries', []):
                vid_id = entry.get('id')
                if not vid_id:
                    continue
                if vid_id in BLOCKED_VIDEO_IDS:
                    continue
                results.append({
                    'id': vid_id,
                    'title': entry.get('title', 'Unknown Title'),
                    'channel': entry.get('uploader') or entry.get('channel', 'YouTube'),
                    'thumbnail': f'https://img.youtube.com/vi/{vid_id}/mqdefault.jpg'
                })
        except Exception as e:
            print('Search Error:', e)
            
    return JsonResponse({'results': results})

def hits(request):
    queries = ['เพลงไทยฮิต', 'เพลงฮิต 2025', 'เพลงดัง', 'เพลงใหม่ 2025', 'เพลงไทยเพราะๆ', 'เพลงฮิตติดชาร์ต']
    query = random.choice(queries)
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'default_search': 'ytsearch10'
    }
    results = []
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch10:{query}', download=False)
            for entry in info.get('entries', []):
                vid_id = entry.get('id')
                if not vid_id:
                    continue
                if vid_id in BLOCKED_VIDEO_IDS:
                    continue
                results.append({
                    'id': vid_id,
                    'title': entry.get('title', 'Unknown Title'),
                    'channel': entry.get('uploader') or entry.get('channel', 'YouTube'),
                    'thumbnail': f'https://img.youtube.com/vi/{vid_id}/mqdefault.jpg'
                })
        except Exception as e:
            print('Hits Error:', e)
    random.shuffle(results)
    return JsonResponse({'results': results[:8]})

@csrf_exempt
def add_to_queue(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        song = SongQueue.objects.create(
            title=data.get('title'),
            video_id=data.get('video_id'),
            thumbnail=data.get('thumbnail'),
            channel=data.get('channel'),
            requested_by=data.get('requested_by', 'ลูกค้าในร้าน'),
            client_id=data.get('client_id', '')
        )
        return JsonResponse({'status': 'success', 'song_id': song.id})
    return JsonResponse({'status': 'failed'}, status=400)

def get_queue(request):
    songs = SongQueue.objects.filter(is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel', 'requested_by'
    )
    return JsonResponse({'queue': list(songs)})

@csrf_exempt
def mark_played(request, song_id):
    SongQueue.objects.filter(id=song_id).update(is_played=True)
    return JsonResponse({'status': 'updated'})

@csrf_exempt
def clear_queue(request):
    SongQueue.objects.all().delete()
    return JsonResponse({'status': 'cleared'})

def my_songs(request):
    client_id = request.GET.get('client_id', '')
    songs = SongQueue.objects.filter(client_id=client_id, is_played=False).values(
        'id', 'title', 'video_id', 'thumbnail', 'channel'
    )
    return JsonResponse({'songs': list(songs)})

@csrf_exempt
def remove_my_song(request, song_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        client_id = data.get('client_id', '')
        deleted = SongQueue.objects.filter(id=song_id, client_id=client_id).delete()[0]
        return JsonResponse({'status': 'deleted' if deleted else 'not_found'})
    return JsonResponse({'status': 'failed'}, status=400)

def generate_qr(request):
    # Use public URL from env var, fallback to request host
    public_url = os.environ.get('PUBLIC_URL')
    if public_url:
        qr_url = f'{public_url.rstrip("/")}/request/'
    else:
        # Build from request host (works on Railway with proper host header)
        scheme = 'https' if request.is_secure() else 'http'
        qr_url = f'{scheme}://{request.get_host()}/request/'
    qr_img = qrcode.make(qr_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')