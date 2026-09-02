# WebSocket Future — Queue Real-time (Django Channels)

> **Status:** docs only, not implemented — for small shop polling 3s is enough. Enable when 20+ concurrent clients.

## Goal
Replace 3s polling (`GET /api/queue/`) with push via Django Channels at `ws/queue/` for instant queue updates.

## Today vs Future

| | Today (polling) | Future (WebSocket) |
|---|---|---|
| Player | `setInterval(fetchQueue, 3000)` | WS `onmessage` -> render |
| Request | `setInterval(updateMyStatus, 3000)` | WS `onmessage` -> update |
| Load 20 clients | 20 req / 3s = 400/min | 1 persistent conn / client |
| Latency | up to 3s | <200ms |

## Stack
- `channels[daphne]` + `channels-redis` (production) / `InMemoryChannelLayer` (dev)
- ASGI via `Daphne` / `Uvicorn`; keep WSGI fallback for now.

## Files to Add/Change

### 1. `music/consumers.py` (new)
```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("queue", self.channel_name)
        await self.accept()
        await self.send_queue()  # push current queue on connect

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("queue", self.channel_name)

    async def queue_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    async def send_queue(self):
        from .models import SongQueue  # lazy import
        from django.forms.models import model_to_dict
        # optional: query async via database_sync_to_async
        pass
```

Broadcast helper (call from views after queue change):
```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_queue():
    channel_layer = get_channel_layer()
    data = {"queue": list(SongQueue.objects.filter(is_played=False).values(...))}
    async_to_sync(channel_layer.group_send)("queue", {"type": "queue.update", "data": data})
```
Call `broadcast_queue()` in `add_to_queue`, `add_to_queue_front`, `mark_played`, `move_queue`, `clear_queue`.

### 2. `music/routing.py` (new)
```python
from django.urls import re_path
from .consumers import QueueConsumer

websocket_urlpatterns = [
    re_path(r"ws/queue/$", QueueConsumer.as_asgi()),
]
```

### 3. `yum_jukebox/asgi.py` (modify)
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import music.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yum_jukebox.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(music.routing.websocket_urlpatterns)),
})
```

### 4. `yum_jukebox/settings.py` (add)
```python
INSTALLED_APPS += ["channels", "daphne"]
ASGI_APPLICATION = "yum_jukebox.asgi.application"
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}  # dev
    # prod: {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [os.environ.get("REDIS_URL")]}}
}
```

### 5. `requirements.txt` (add)
```
channels[daphne]==4.2.0
channels-redis==4.2.0
```

## Endpoint
- `ws/queue/` — single group `queue`. Auth not required for read; write still via HTTP POST + broadcast. Optional owner-only filter later.

## Replace Polling 3s

**Player (`player.html`):**
```js
// delete: setInterval(fetchQueue, 3000)
// add:
const ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/queue/");
ws.onmessage = (e) => { const data=JSON.parse(e.data); renderQueue(data.queue); if(data.queue.length && !player) playNext(); };
ws.onclose = () => setTimeout(()=> location.reload(), 3000); // fallback to polling/reconnect
```

**Request (`request.html`):**
```js
const ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/queue/");
ws.onmessage = (e) => updateMyStatus(JSON.parse(e.data));
```

Fallback: if `WebSocket` fails, keep `setInterval(fetchQueue, 3000)` as degraded mode.

## Rollout Steps
1. `pip install channels[daphne] channels-redis`; `python manage.py check` pass.
2. Add files above, run `daphne yum_jukebox.asgi:application`.
3. Wire `broadcast_queue()` into 5 queue views.
4. Frontend switch polling -> WS, keep polling fallback.
5. Load test 30 clients, verify `queue.update` latency.

## When to Build
- Queue >20 concurrent or render latency noticed. Until then polling 3s is cheap and simple.

## Verify
```
python manage.py check
python manage.py test  # no WS tests yet
```
