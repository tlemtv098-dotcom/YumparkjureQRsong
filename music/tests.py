import json
from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User

LOGO = '/static/music/img/logo.jpg'


class PlayerPageTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='player_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)

    def test_player_requires_login_anon_redirect(self):
        self.client.logout()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=/', response.url)

    def test_player_allows_staff(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_player_page_renders(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_player_has_logo(self):
        response = self.client.get('/')
        self.assertContains(response, LOGO)

    def test_player_has_idle_splash(self):
        response = self.client.get('/')
        self.assertContains(response, 'id=\"idle-splash\"')

    def test_player_has_core_elements(self):
        response = self.client.get('/')
        for token in ['id=\"player\"', 'id=\"queue-list\"', 'id=\"queue-count\"',
                      'id=\"now-playing-title\"', 'src=\"/qr.png\"']:
            self.assertContains(response, token)

    def test_player_has_clear_queue_button(self):
        response = self.client.get('/')
        self.assertContains(response, 'clearQueue')
        self.assertContains(response, 'รีคิวเพลง')

    def test_player_has_wake_lock(self):
        response = self.client.get('/')
        self.assertContains(response, 'wakeLock')

    def test_player_has_auto_play(self):
        response = self.client.get('/')
        self.assertContains(response, 'function playNext')
        self.assertContains(response, 'player.mute()')
        self.assertContains(response, 'player.unMute()')
        self.assertContains(response, 'lastPlayedVideoId')
        self.assertNotContains(response, 'onclick=\"playSong(')
        self.assertNotContains(response, '▶')

    def test_player_has_auto_next_on_end(self):
        response = self.client.get('/')
        self.assertContains(response, 'onPlayerStateChange')
        self.assertContains(response, 'ENDED')
        self.assertContains(response, 'removePlayedSong')

    def test_player_has_ensure_playing(self):
        response = self.client.get('/')
        self.assertContains(response, 'ensurePlaying')
        self.assertContains(response, 'playVideo()')

    def test_player_has_no_action_emojis(self):
        response = self.client.get('/')
        self.assertNotContains(response, '🎵 สแกน QR เพื่อขอเพลง')
        self.assertNotContains(response, 'ข้ามเพลง ⏭️')
        self.assertNotContains(response, '📲 สแกนเพื่อขอเพลง')

    def test_player_has_volume_control(self):
        response = self.client.get('/')
        self.assertContains(response, 'volume-slider')
        self.assertContains(response, 'auto-random-btn')
        self.assertContains(response, 'toggleAutoRandom')
        self.assertContains(response, 'showToast')


class RequestPageTests(TestCase):
    def test_request_page_renders(self):
        response = self.client.get('/request/')
        self.assertEqual(response.status_code, 200)

    def test_request_has_logo(self):
        response = self.client.get('/request/')
        self.assertContains(response, LOGO)

    def test_request_has_no_old_images(self):
        response = self.client.get('/request/')
        self.assertNotContains(response, '/static/music/img/2.png')
        self.assertNotContains(response, '/static/music/img/2.jpg')

    def test_request_has_form_elements(self):
        response = self.client.get('/request/')
        for token in ['id=\"searchInput\"', 'id=\"results\"', 'id=\"loading\"']:
            self.assertContains(response, token)

    def test_request_has_no_comment_field(self):
        response = self.client.get('/request/')
        self.assertNotContains(response, 'id=\"comment\"')

    def test_request_has_hit_list(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'id=\"hit-list\"')
        self.assertContains(response, 'เพลง')

    def test_request_has_refresh_hits(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'id=\"refresh-hits\"')
        self.assertContains(response, 'fetchHits')
        self.assertContains(response, 'รีเฟรชเพลง')

    def test_request_has_result_panel_with_status(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'id="result-panel"')
        self.assertContains(response, 'mySongId')
        self.assertContains(response, 'updateMyStatus')
        self.assertContains(response, 'คิวของคุณ')
        self.assertNotContains(response, 'กำลังเล่นเพลงนี้เลย')
        self.assertContains(response, '60000')

    def test_request_has_live_search(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'addEventListener')
        self.assertContains(response, 'searchTimer')

    def test_request_has_no_refresh_emoji(self):
        response = self.client.get('/request/')
        self.assertNotContains(response, '🔄 รีเฟรชเพลง')

    def test_request_has_next_up_card(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'id=\"now-playing-card\"')
        self.assertContains(response, 'fetchNowPlaying')
        self.assertContains(response, 'เพลงถัดไป')

    def test_request_has_my_songs_section(self):
        response = self.client.get('/request/')
        self.assertContains(response, 'id=\"my-songs-list\"')
        self.assertContains(response, 'เพลงที่ฉันขอ')
        self.assertContains(response, 'clientId')
        self.assertContains(response, 'localStorage')
        self.assertContains(response, 'removeMySong')

    def test_request_has_no_checkbox(self):
        response = self.client.get('/request/')
        self.assertNotContains(response, 'hit-checkbox')
        self.assertNotContains(response, 'new-checkbox')
    def test_request_has_genre_tabs(self):
        response = self.client.get('/request/')
        # Tabs removed per 2026-09-07 plan - request should NOT have genre tabs
        self.assertNotContains(response, 'genre-tab')


class ClearQueueApiTests(TestCase):
    def test_clear_queue_requires_owner(self):
        from .models import SongQueue
        SongQueue.objects.create(title='A', video_id='a', thumbnail='', channel='', requested_by='x')
        response = self.client.post('/api/clear/')
        self.assertEqual(response.status_code, 403)
        response = self.client.post('/api/clear/', headers={'X-Player-Token': 'wrong-token'})
        self.assertEqual(response.status_code, 403)

    def test_clear_queue_empties_songs(self):
        from .models import SongQueue
        SongQueue.objects.create(title='A', video_id='a', thumbnail='', channel='', requested_by='x')
        SongQueue.objects.create(title='B', video_id='b', thumbnail='', channel='', requested_by='y')
        response = self.client.post('/api/clear/', headers={'X-Player-Token': settings.PLAYER_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SongQueue.objects.count(), 0)

    def test_clear_queue_with_csrf_and_owner(self):
        from django.test import Client
        from .models import SongQueue
        SongQueue.objects.create(title='C', video_id='c', thumbnail='', channel='', requested_by='z')
        client = Client(enforce_csrf_checks=True)
        # without csrf and without owner -> 403 (csrf or forbidden, both deny)
        res = client.post('/api/clear/')
        self.assertEqual(res.status_code, 403)
        # get csrf token
        client.get('/request/')
        csrf_token = client.cookies['csrftoken'].value
        # with csrf but without owner -> 403 forbidden
        res = client.post('/api/clear/', headers={'X-CSRFToken': csrf_token, 'X-Player-Token': 'wrong'})
        self.assertEqual(res.status_code, 403)
        # with csrf and correct owner -> 200
        res = client.post('/api/clear/', headers={'X-CSRFToken': csrf_token, 'X-Player-Token': settings.PLAYER_TOKEN})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(SongQueue.objects.count(), 0)

class MarkPlayedApiTests(TestCase):
    def test_mark_played_requires_owner(self):
        from .models import SongQueue
        song = SongQueue.objects.create(title='A', video_id='a', thumbnail='', channel='', requested_by='x')
        response = self.client.get(f'/api/played/{song.id}/')
        self.assertEqual(response.status_code, 403)
        response = self.client.get(f'/api/played/{song.id}/', headers={'X-Player-Token': settings.PLAYER_TOKEN})
        self.assertEqual(response.status_code, 200)
        song.refresh_from_db()
        self.assertTrue(song.is_played)


class MySongsApiTests(TestCase):
    def test_add_stores_client_id(self):
        from .models import SongQueue
        response = self.client.post('/api/add/', data=json.dumps({
            'title': 'A', 'video_id': 'a', 'thumbnail': '', 'channel': 'c', 'client_id': 'abc'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SongQueue.objects.get(video_id='a').client_id, 'abc')

    def test_my_songs_returns_only_own(self):
        from .models import SongQueue
        SongQueue.objects.create(title='Mine', video_id='m', thumbnail='', channel='', client_id='me')
        SongQueue.objects.create(title='Other', video_id='o', thumbnail='', channel='', client_id='them')
        response = self.client.get('/api/my-songs/?client_id=me')
        self.assertEqual(response.status_code, 200)
        songs = response.json()['songs']
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0]['title'], 'Mine')

    def test_remove_my_song_deletes_own(self):
        from .models import SongQueue
        song = SongQueue.objects.create(title='Mine', video_id='m', thumbnail='', channel='', client_id='me')
        response = self.client.post(f'/api/my-songs/{song.id}/delete/', data=json.dumps({'client_id': 'me'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'deleted')
        self.assertEqual(SongQueue.objects.filter(id=song.id).count(), 0)

    def test_remove_my_song_cannot_delete_others(self):
        from .models import SongQueue
        song = SongQueue.objects.create(title='Other', video_id='o', thumbnail='', channel='', client_id='them')
        response = self.client.post(f'/api/my-songs/{song.id}/delete/', data=json.dumps({'client_id': 'me'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'not_found')
        self.assertEqual(SongQueue.objects.filter(id=song.id).count(), 1)

class HealthzTests(TestCase):
    def test_healthz_ok(self):
        self.assertEqual(self.client.get('/healthz/').status_code, 200)
        self.assertEqual(self.client.get('/healthz/').json()['status'], 'ok')

class StatsTests(TestCase):
    def test_stats_ok(self):
        from .models import SongQueue
        SongQueue.objects.create(title='A', video_id='a', thumbnail='', channel='c')
        res = self.client.get('/api/stats/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('total_queued', data)
        self.assertIn('top_songs', data)

class SuggestTests(TestCase):
    def test_suggest_empty_q(self):
        self.assertEqual(self.client.get('/api/suggest/?q=').json()['suggestions'], [])
    def test_suggest_short_q(self):
        self.assertEqual(self.client.get('/api/suggest/?q=a').json()['suggestions'], [])
    def test_suggest_returns_list(self):
        res = self.client.get('/api/suggest/?q=เพลง')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json()['suggestions'], list)

class DedupTests(TestCase):
    def setUp(self):
        from .views import _rate_limit_store
        _rate_limit_store.clear()
    def test_dedup_same_video(self):
        self.client.post('/api/add/', data=json.dumps({'title':'A','video_id':'dup123','thumbnail':'','channel':'c','client_id':'c1'}), content_type='application/json')
        res = self.client.post('/api/add/', data=json.dumps({'title':'A','video_id':'dup123','thumbnail':'','channel':'c','client_id':'c1'}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('อยู่ในคิว', res.json()['error'])

class QueueLimitTests(TestCase):
    def setUp(self):
        from .views import _rate_limit_store
        _rate_limit_store.clear()
    def test_per_client_limit(self):
        for i in range(5):
            self.client.post('/api/add/', data=json.dumps({'title':f'A{i}','video_id':f'vid{i}','thumbnail':'','channel':'c','client_id':'limit_client'}), content_type='application/json')
        res = self.client.post('/api/add/', data=json.dumps({'title':'A5','video_id':'vid5','thumbnail':'','channel':'c','client_id':'limit_client'}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('5 เพลง', res.json()['error'])

class QueueApiTests(TestCase):
    def test_queue_returns_list(self):
        from .models import SongQueue
        SongQueue.objects.create(title='Q', video_id='q1', thumbnail='', channel='c')
        res = self.client.get('/api/queue/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('queue', res.json())

class PwaTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='pwa_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_manifest_static_exists(self):
        # manifest should be served via static, but template link should exist
        res = self.client.get('/')
        self.assertContains(res, 'manifest.json')
        self.assertContains(res, 'serviceWorker')
    def test_request_has_pwa(self):
        res = self.client.get('/request/')
        self.assertContains(res, 'manifest.json')

class ErrorPagesTests(TestCase):
    def test_404_template_exists(self):
        import os
        from django.conf import settings
        self.assertTrue(os.path.exists(os.path.join(settings.BASE_DIR, 'music', 'templates', '404.html')))
    def test_500_template_removed(self):
        import os
        from django.conf import settings
        self.assertFalse(os.path.exists(os.path.join(settings.BASE_DIR, 'music', 'templates', '500.html')))


# --- Task 4: Regression tests for universal platform support ---
class UniversalHitsRegressionTests(TestCase):
    def test_api_hits_never_returns_blocked_ids(self):
        from unittest.mock import patch
        from django.core.cache import cache
        from music.views import BLOCKED_VIDEO_IDS
        cache.clear()
        blocked_id = next(iter(BLOCKED_VIDEO_IDS))
        # Case 1: fallback path (search_youtube returns [] -> static fallback)
        with patch('music.views.search_youtube', return_value=[]):
            cache.clear()
            res = self.client.get('/api/hits/?player=1')
            self.assertEqual(res.status_code, 200)
            ids = [r['id'] for r in res.json().get('results', [])]
            for bid in BLOCKED_VIDEO_IDS:
                self.assertNotIn(bid, ids, f'blocked id {bid} leaked in hits fallback')
        # Case 2: live results containing blocked id should be filtered (defense in depth)
        mixed = [
            {'id': blocked_id, 'title': 'Blocked', 'channel': 'X', 'thumbnail': 'https://img.youtube.com/vi/%s/mqdefault.jpg' % blocked_id},
            {'id': 'ks7p6DA0dKk', 'title': 'Good', 'channel': 'Y', 'thumbnail': 'https://img.youtube.com/vi/ks7p6DA0dKk/mqdefault.jpg'},
        ]
        with patch('music.views.search_youtube', return_value=mixed):
            cache.clear()
            res = self.client.get('/api/hits/')
            self.assertEqual(res.status_code, 200)
            ids = [r['id'] for r in res.json().get('results', [])]
            self.assertNotIn(blocked_id, ids)
            for bid in BLOCKED_VIDEO_IDS:
                self.assertNotIn(bid, ids)


class UniversalSearchRegressionTests(TestCase):
    def test_api_search_never_returns_blocked_ids(self):
        from unittest.mock import patch
        from django.core.cache import cache
        from music.views import BLOCKED_VIDEO_IDS
        cache.clear()
        # Fallback path when search_youtube returns [] — should return filtered static list
        with patch('music.views.search_youtube', return_value=[]):
            res = self.client.get('/api/search/?q=เพลง')
            self.assertEqual(res.status_code, 200)
            ids = [r['id'] for r in res.json().get('results', [])]
            for bid in BLOCKED_VIDEO_IDS:
                self.assertNotIn(bid, ids, f'blocked id {bid} leaked in search fallback')
            # also test arbitrary query that triggers fallback[:3]
            res2 = self.client.get('/api/search/?q=xyz-no-match-123')
            ids2 = [r['id'] for r in res2.json().get('results', [])]
            for bid in BLOCKED_VIDEO_IDS:
                self.assertNotIn(bid, ids2)
        # Also test search_youtube itself filters blocked even when raw has blocked
        # mock yt-dlp path: youtube_api_search returns [] and raw contains blocked
        from unittest.mock import MagicMock
        blocked_id = next(iter(BLOCKED_VIDEO_IDS))
        mock_info = {
            'entries': [
                {'id': blocked_id, 'title': 'Blocked Song', 'uploader': 'GMM'},
                {'id': 'ks7p6DA0dKk', 'title': 'Good Song', 'uploader': 'GeneLab'},
            ]
        }
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_ydl_class = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_class.return_value.__exit__.return_value = False
        with patch('music.views.youtube_api_search', return_value=[]), \
             patch('music.views.YoutubeDL', mock_ydl_class), \
             patch('music.views._is_embeddable', return_value=True):
            from music.views import search_youtube
            results = search_youtube('test', 5)
            ids = [r['id'] for r in results]
            self.assertNotIn(blocked_id, ids)


class UniversalPlayerRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='uni_player_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_player_no_autoplay_without_tap_gate(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn('sound-overlay', content)
        self.assertNotIn('queue-overlay', content)
        self.assertIn('isLineWebView', content)
        self.assertIn('เปิดในเบราว์เซอร์', content)
        self.assertNotIn('isMobile && !userInteracted', content)

    def test_player_has_uniform_tap_gate(self):
        res = self.client.get('/')
        content = res.content.decode()
        self.assertIn('sound-overlay', content)
        self.assertNotIn('queue-overlay', content)
        self.assertIn('isLineWebView', content)
        self.assertIn('เปิดในเบราว์เซอร์', content)
        self.assertNotIn('isMobile && !userInteracted', content)


class SingleSoundOverlayTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='sound_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_only_sound_overlay_exists(self):
        res = self.client.get('/')
        content = res.content.decode()
        self.assertIn('id="sound-overlay"', content)
        self.assertNotIn('id="queue-overlay"', content)


class SearchFastFallbackRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='fast_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_search_returns_fast_when_api_empty(self):
        import time
        from unittest.mock import patch
        with patch('music.views.youtube_api_search', return_value=[]):
            start = time.time()
            res = self.client.get('/api/search/?q=ข้างกัน')
            elapsed = time.time() - start
            self.assertEqual(res.status_code, 200)
            self.assertLess(elapsed, 5)
            self.assertIsInstance(res.json()['results'], list)

    def test_player_search_has_abort(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('AbortController', html)
        self.assertIn('manual-loading', html)

    def test_request_search_has_abort(self):
        res = self.client.get('/request/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('AbortController', html)
        self.assertIn('loading', html)


class SearchColdstartRetryRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='cold_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_player_search_retries_once_and_thai_message(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('manualSearchRetry', html)
        self.assertIn('เชื่อมต่อเซิร์ฟเวอร์ไม่สำเร็จ', html)

    def test_request_search_retries_once(self):
        res = self.client.get('/request/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('searchRetry', html)


class FallbackIdsRegressionTests(TestCase):
    def test_hits_fallback_ids_are_valid_youtube_ids(self):
        import re
        from unittest.mock import patch
        from django.core.cache import cache
        cache.clear()
        with patch('music.views.search_youtube', return_value=[]):
            cache.clear()
            res = self.client.get('/api/hits/')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertGreater(len(results), 0)
            for r in results:
                self.assertRegex(r['id'], r'^[A-Za-z0-9_-]{11}$')

    def test_hits_fallback_thumbnails_contain_own_id(self):
        from unittest.mock import patch
        from django.core.cache import cache
        cache.clear()
        with patch('music.views.search_youtube', return_value=[]):
            cache.clear()
            res = self.client.get('/api/hits/')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertGreater(len(results), 0)
            for r in results:
                self.assertIn(r['id'], r.get('thumbnail', ''))


class FallbackMismatchRegressionTests(TestCase):
    def test_hits_fallback_has_no_mismatched_ids(self):
        from unittest.mock import patch
        from django.core.cache import cache
        cache.clear()
        with patch('music.views.search_youtube', return_value=[]):
            cache.clear()
            res = self.client.get('/api/hits/')
            self.assertEqual(res.status_code, 200)
            ids = [r['id'] for r in res.json().get('results', [])]
            self.assertNotIn('9bZkp7q19f0', ids)
            self.assertNotIn('kJQP7kiw5Fk', ids)


class ApiKeyRotationRegressionTests(TestCase):
    def _success_response(self, video_id='ks7p6DA0dKk'):
        import json as json_lib
        from unittest.mock import MagicMock
        payload = {
            'items': [
                {
                    'id': {'videoId': video_id},
                    'snippet': {
                        'title': 'Test Song',
                        'channelTitle': 'Test Channel',
                        'thumbnails': {'medium': {'url': 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id}},
                    },
                }
            ]
        }
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json_lib.dumps(payload).encode('utf-8')
        return response

    def test_rotation_on_quota_uses_second_key(self):
        import io
        import os
        import urllib.error
        from unittest.mock import patch
        from music.views import youtube_api_search
        quota_body = b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        quota_error = urllib.error.HTTPError(
            'https://www.googleapis.com/youtube/v3/search', 403,
            'Forbidden', {}, io.BytesIO(quota_body),
        )
        env = {
            'YOUTUBE_API_KEYS': 'TESTKEY1,TESTKEY2',
            'YOUTUBE_API_KEY': '',
            'key': '',
            'YOUTUBE_API_KEY_2': '',
        }
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen',
                       side_effect=[quota_error, self._success_response()]) as mock_urlopen, \
                 patch('music.views._is_embed_ok', return_value=True):
                results = youtube_api_search('test song', 5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'ks7p6DA0dKk')
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_network_error_tries_next_key(self):
        import os
        import urllib.error
        from unittest.mock import patch
        from music.views import youtube_api_search
        env = {
            'YOUTUBE_API_KEYS': 'TESTKEY1,TESTKEY2',
            'YOUTUBE_API_KEY': '',
            'key': '',
            'YOUTUBE_API_KEY_2': '',
        }
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen',
                       side_effect=[urllib.error.URLError('timed out'),
                                    self._success_response()]) as mock_urlopen, \
                 patch('music.views._is_embed_ok', return_value=True):
                results = youtube_api_search('test song', 5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'ks7p6DA0dKk')
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_single_invalid_key_returns_empty_without_looping(self):
        import io
        import os
        import urllib.error
        from unittest.mock import patch
        from music.views import youtube_api_search
        invalid_body = b'{"error": {"errors": [{"reason": "keyInvalid"}]}}'
        invalid_error = urllib.error.HTTPError(
            'https://www.googleapis.com/youtube/v3/search', 400,
            'Bad Request', {}, io.BytesIO(invalid_body),
        )
        env = {
            'YOUTUBE_API_KEYS': 'TESTKEY1',
            'YOUTUBE_API_KEY': '',
            'key': '',
            'YOUTUBE_API_KEY_2': '',
        }
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen',
                       side_effect=invalid_error) as mock_urlopen:
                results = youtube_api_search('test song', 5)
        self.assertEqual(results, [])
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_no_hardcoded_real_key_in_views(self):
        import os
        from django.conf import settings
        views_path = os.path.join(settings.BASE_DIR, 'music', 'views.py')
        with open(views_path, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertEqual(source.count('AIza'), 0)


class FallbackPoolRegressionTests(TestCase):
    def test_search_fallback_pool_has_at_least_10_entries(self):
        from unittest.mock import patch
        with patch('music.views.youtube_api_search', return_value=[]):
            # Nonsense query hits the fallback[:3] path — proves fallback active.
            res = self.client.get('/api/search/?q=xyz-no-match-123-qwerty-999')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertIsInstance(results, list)
            self.assertGreaterEqual(len(results), 3)
            # Broad query matching most pool entries proves pool expanded to >= 10.
            res_all = self.client.get('/api/search/?q=-')
            self.assertEqual(res_all.status_code, 200)
            pool_results = res_all.json().get('results', [])
            self.assertGreaterEqual(len(pool_results), 10)

    def test_search_fallback_relevance_for_love_query(self):
        from unittest.mock import patch
        with patch('music.views.youtube_api_search', return_value=[]):
            res = self.client.get('/api/search/?q=เพลงรัก')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertGreater(len(results), 0)
            self.assertTrue(
                any('รัก' in r.get('title', '') for r in results),
                'expected at least one fallback title containing รัก for query เพลงรัก',
            )


class SearchButtonsWrapRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='wrap_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_search_buttons_wrap(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('flex-wrap', html)
        self.assertIn('w-full md:w-auto', html)


class FallbackUnblockRegressionTests(TestCase):
    def test_block_fallback_id_skipped(self):
        from .models import BlockedVideo
        res = self.client.post('/api/block/ks7p6DA0dKk/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'skipped')
        self.assertEqual(BlockedVideo.objects.filter(video_id='ks7p6DA0dKk').count(), 0)

    def test_clear_blocked_clears_all(self):
        from .models import BlockedVideo
        BlockedVideo.objects.create(video_id='ks7p6DA0dKk', reason='Error 153')
        BlockedVideo.objects.create(video_id='ZZZZZZZZZZZ', reason='Error 153')
        BlockedVideo.objects.create(video_id='YYYYYYYYYYY', reason='Error 153')
        # without token -> 403, rows untouched
        res = self.client.post('/api/block/clear/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(BlockedVideo.objects.count(), 3)
        # owner clears all rows
        res = self.client.post('/api/block/clear/', headers={'X-Player-Token': settings.PLAYER_TOKEN})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['deleted'], 3)
        self.assertEqual(BlockedVideo.objects.count(), 0)

    def test_hits_fallback_not_filtered_by_non_fallback_db_blocks(self):
        from unittest.mock import patch
        from django.core.cache import cache
        from .models import BlockedVideo
        from .views import FALLBACK_IDS
        cache.clear()
        BlockedVideo.objects.create(video_id='ZZZZZZZZZZZ', reason='Error 153')
        with patch('music.views.search_youtube', return_value=[]):
            cache.clear()
            res = self.client.get('/api/hits/')
            self.assertEqual(res.status_code, 200)
            ids = [r['id'] for r in res.json().get('results', [])]
            self.assertGreater(len(ids), 0)
            for fid in FALLBACK_IDS:
                self.assertIn(fid, ids, f'fallback id {fid} missing from hits')


class Error153BreakerRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='breaker_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_153_breaker_counter_and_reset_markers(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'consecutive153')
        self.assertContains(res, 'consecutive153 = 0')
        self.assertContains(res, 'consecutive153++')
        self.assertContains(res, 'consecutive153 >= 3')
        self.assertContains(res, 'handleOverlayTap')
        self.assertContains(res, 'YT.PlayerState.PLAYING')
        self.assertContains(res, 'sound-overlay')
        self.assertContains(res, 'แตะเพื่อลองใหม่')


class BreakerTripSkipRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='trip_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_breaker_trip_skips_song(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        trip_idx = html.find('consecutive153 >= 3')
        self.assertNotEqual(trip_idx, -1, 'trip branch marker missing')
        return_idx = html.find('return', trip_idx)
        self.assertNotEqual(return_idx, -1, 'trip branch return missing')
        trip_block = html[trip_idx:return_idx]
        self.assertIn('skipSong()', trip_block)


class BreakerFullStopRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='fullstop_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_breaker_full_stop_markers(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        # flag declared
        self.assertIn('let breakerTripped = false', html)
        # trip branch sets flag
        trip_idx = html.find('consecutive153 >= 3')
        self.assertNotEqual(trip_idx, -1, 'trip branch marker missing')
        self.assertIn('breakerTripped = true', html[trip_idx:trip_idx + 800])
        # autoplay guard blocks full-stop
        self.assertIn('if (breakerTripped) return', html)
        # tap handler clears flag
        tap_idx = html.find('function handleOverlayTap')
        self.assertNotEqual(tap_idx, -1, 'tap handler missing')
        self.assertIn('breakerTripped = false', html[tap_idx:tap_idx + 800])
        # PLAYING success clears flag
        playing_idx = html.find('event.data === YT.PlayerState.PLAYING')
        self.assertNotEqual(playing_idx, -1, 'PLAYING marker missing')
        self.assertIn('breakerTripped = false', html[playing_idx:playing_idx + 800])


class EmbedTestPageTests(TestCase):
    def test_embed_test_page_renders_with_nocookie_iframe(self):
        res = self.client.get('/embed-test/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'youtube-nocookie.com/embed/ks7p6DA0dKk')

    def test_embed_test_has_api_section(self):
        res = self.client.get('/embed-test/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'loadVideoById')

    def test_embed_test_has_prefilled_section(self):
        res = self.client.get('/embed-test/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'prefilled-player')
        self.assertContains(res, 'videoId')

    def test_embed_test_has_noorigin_section(self):
        res = self.client.get('/embed-test/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'noorigin-player')


class FullPlayerVarsRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='fullvars_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_player_full_vars(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        # Full 9-var set from playervars-revert Task 1
        self.assertContains(res, "'enablejsapi': 1")
        self.assertContains(res, "'mute': 1")
        self.assertContains(res, "'playsinline': 1")
        self.assertContains(res, "'autoplay': 1")
        self.assertContains(res, "'controls': 1")
        self.assertContains(res, "'modestbranding': 1")
        self.assertContains(res, "'rel': 0")
        self.assertContains(res, "'iv_load_policy': 3")
        self.assertContains(res, "'fs': 1")


class NoApiModeRegressionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='noapi_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)
    def test_duration_valid_id_returns_int(self):
        res = self.client.get('/api/duration/?id=ks7p6DA0dKk')
        self.assertEqual(res.status_code, 200)
        self.assertIn('duration_sec', res.json())
        self.assertIsInstance(res.json()['duration_sec'], int)

    def test_duration_invalid_id_returns_180(self):
        res = self.client.get('/api/duration/?id=bad')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['duration_sec'], 180)

    def test_player_has_noapi_markers(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'NOAPI_MODE')
        self.assertContains(res, 'playNextNoApi')

    def test_noapi_retry_guarded_by_no_current_song(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('window.noapiTimer', html)
        self.assertIn('if (!currentSong) playNextNoApi()', html)


class AlbumAllowedRegressionTests(TestCase):
    """Album titles (Longplay, รวมเพลง, ชั่วโมง, อัลบั้ม, etc.) must pass through search/hits."""

    def test_search_allows_album_title(self):
        from unittest.mock import patch
        # Mock youtube_api_search to return an album-like title
        album_item = {
            'id': 'album1234567',
            'title': 'Longplay รวมเพลงฮิต 2025 ชั่วโมงเต็ม',
            'channel': 'Test Channel',
            'thumbnail': 'https://i.ytimg.com/vi/album1234567/hqdefault.jpg',
        }
        with patch('music.views.youtube_api_search', return_value=[album_item]):
            res = self.client.get('/api/search/?q=longplay')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertGreater(len(results), 0)
            # Album title should NOT be filtered out
            self.assertEqual(results[0]['id'], 'album1234567')
            self.assertIn('Longplay', results[0]['title'])

    def test_hits_allows_album_title(self):
        from unittest.mock import patch
        from django.core.cache import cache
        # Mock search_youtube to return an album-like title
        album_item = {
            'id': 'album7654321',
            'title': 'อัลบั้มรวมเพลง 60 minutes non-stop',
            'channel': 'Test Channel',
            'thumbnail': 'https://i.ytimg.com/vi/album7654321/hqdefault.jpg',
        }
        # Force cache miss and mock search_youtube
        with patch('music.views.search_youtube', return_value=[album_item]), \
             patch('music.views.cache.get', return_value=None):
            cache.clear()
            res = self.client.get('/api/hits/?player=1')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            self.assertGreater(len(results), 0)
            # Album title should NOT be filtered out for player (with ?player=1)
            ids = [r['id'] for r in results]
            self.assertIn('album7654321', ids)
            album_result = next(r for r in results if r['id'] == 'album7654321')
            self.assertIn('อัลบั้ม', album_result['title'])

class AuthRegressionTests(TestCase):
    def test_player_requires_login_anon_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertTrue(response.url.startswith('/accounts/login/?next=/'))

    def test_player_allows_staff(self):
        staff = User.objects.create_user(username='auth_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_request_still_public_anon_200(self):
        response = self.client.get('/request/')
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_staff_and_redirects_to_login(self):
        response = self.client.post('/accounts/signup/', {'username': 'owner1', 'password1': 'Testpass123!', 'password2': 'Testpass123!'})
        # signup should redirect to login (not auto-login)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/')
        user = User.objects.get(username='owner1')
        self.assertTrue(user.is_staff)
        # client should NOT be authenticated after signup (must login)
        self.assertNotIn('_auth_user_id', self.client.session)
        # after login, staff can access player
        self.client.post('/accounts/login/', {'username': 'owner1', 'password': 'Testpass123!'})
        resp2 = self.client.get('/')
        self.assertEqual(resp2.status_code, 200)

    def test_login_success(self):
        User.objects.create_user(username='owner2', password='Testpass123!', is_staff=True)
        response = self.client.post('/accounts/login/', {'username': 'owner2', 'password': 'Testpass123!'})
        self.assertEqual(response.status_code, 302)
        # after login, GET / should be 200
        resp2 = self.client.get('/')
        self.assertEqual(resp2.status_code, 200)

    def test_logout_via_post(self):
        staff = User.objects.create_user(username='stafflogout', password='Testpass123!', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/').status_code, 200)
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        # after logout, anon should be redirected
        resp2 = self.client.get('/')
        self.assertEqual(resp2.status_code, 302)


class PlaylistAccountTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='playlist_a', password='Testpass123!', is_staff=True)
        self.user_b = User.objects.create_user(username='playlist_b', password='Testpass123!', is_staff=True)

    def test_playlist_persists_across_sessions(self):
        # login as user_a, create playlist via API, check persists after re-login (simulate second device)
        self.client.force_login(self.user_a)
        resp = self.client.post('/api/playlists/create/', data=json.dumps({'name': 'MyPlaylist', 'songs': [{'id': 'abc12345678', 'title': 'Test Song', 'channel': 'Test', 'thumbnail': '', 'video_id': 'abc12345678'}]}), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['name'], 'MyPlaylist')
        # check exists
        resp2 = self.client.get('/api/playlists/')
        self.assertEqual(resp2.status_code, 200)
        names = [p['name'] for p in resp2.json()['playlists']]
        self.assertIn('MyPlaylist', names)
        # simulate second device: logout and login same user
        self.client.logout()
        self.client.force_login(self.user_a)
        resp3 = self.client.get('/api/playlists/')
        self.assertEqual(resp3.status_code, 200)
        names3 = [p['name'] for p in resp3.json()['playlists']]
        self.assertIn('MyPlaylist', names3)

    def test_playlist_isolation_between_users(self):
        # user_a creates playlist
        self.client.force_login(self.user_a)
        self.client.post('/api/playlists/create/', data=json.dumps({'name': 'A Playlist', 'songs': [{'id': 'a1b2c3d4e5f', 'title': 'A Song'}]}), content_type='application/json')
        self.client.logout()
        # user_b should see empty
        self.client.force_login(self.user_b)
        resp = self.client.get('/api/playlists/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['playlists']), 0)
        # user_b creates own
        self.client.post('/api/playlists/create/', data=json.dumps({'name': 'B Playlist', 'songs': []}), content_type='application/json')
        resp2 = self.client.get('/api/playlists/')
        names_b = [p['name'] for p in resp2.json()['playlists']]
        self.assertIn('B Playlist', names_b)
        self.assertNotIn('A Playlist', names_b)
        # back to user_a should still only see A
        self.client.logout()
        self.client.force_login(self.user_a)
        resp3 = self.client.get('/api/playlists/')
        names_a = [p['name'] for p in resp3.json()['playlists']]
        self.assertIn('A Playlist', names_a)
        self.assertNotIn('B Playlist', names_a)

    def test_local_fallback_when_anon(self):
        # anon GET should redirect to login (302), not 200
        self.client.logout()
        resp = self.client.get('/api/playlists/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login/', resp.url)
        # anon POST should also redirect
        resp2 = self.client.post('/api/playlists/create/', data=json.dumps({'name': 'Anon', 'songs': []}), content_type='application/json')
        self.assertEqual(resp2.status_code, 302)

    def test_migrate_local_to_account_duplicate_ignored(self):
        # Simulate migration: local playlists POSTed, duplicate ignored (400)
        self.client.force_login(self.user_a)
        self.client.post('/api/playlists/create/', data=json.dumps({'name': 'Dupe', 'songs': [{'id': 'dup12345678', 'title': 'X'}]}), content_type='application/json')
        # second POST same name should be 400 duplicate
        resp = self.client.post('/api/playlists/create/', data=json.dumps({'name': 'Dupe', 'songs': [{'id': 'dup12345678', 'title': 'X'}]}), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('already exists', resp.json()['error'])
        # only one remains
        resp2 = self.client.get('/api/playlists/')
        dupe_count = [p for p in resp2.json()['playlists'] if p['name'] == 'Dupe']
        self.assertEqual(len(dupe_count), 1)


class NoApiMuteRegressionTests(TestCase):
    def test_noapi_iframe_muted_autoplay(self):
        self.client.force_login(User.objects.create_user(username='nm1', password='Testpass123!', is_staff=True))
        html = self.client.get('/?noapi=1').content.decode()
        self.assertIn('autoplay=1&mute=1', html)
    def test_noapi_iframe_has_origin(self):
        self.client.force_login(User.objects.create_user(username='nm2', password='Testpass123!', is_staff=True))
        html = self.client.get('/?noapi=1').content.decode()
        self.assertIn('enablejsapi=1&origin=', html)

class NoApiQuickSkipRegressionTests(TestCase):
    def test_no_auto_skip_in_noapi(self):
        self.client.force_login(User.objects.create_user(username='nq1', password='Testpass123!', is_staff=True))
        html = self.client.get('/').content.decode()
        self.assertNotIn('suspect 153 id, skipping quickly', html)

class UnblockApiTests(TestCase):
    def test_unblock_requires_owner(self):
        resp = self.client.delete('/api/unblock/abc123/')
        self.assertEqual(resp.status_code, 403)
    def test_unblock_removes_block(self):
        from music.models import BlockedVideo
        staff = User.objects.create_user(username='ub1', password='Testpass123!', is_staff=True)
        self.client.force_login(staff)
        BlockedVideo.objects.create(video_id='yEbv0QiI1Ns')
        resp = self.client.delete('/api/unblock/yEbv0QiI1Ns/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(BlockedVideo.objects.filter(video_id='yEbv0QiI1Ns').exists())

class WidgetReferrerRegressionTests(TestCase):
    def test_no_undefined_widget_referrer(self):
        self.client.force_login(User.objects.create_user(username='wr1', password='Testpass123!', is_staff=True))
        html = self.client.get('/').content.decode()
        self.assertNotIn('widget_referrer', html)
        self.assertIn("host: 'https://www.youtube-nocookie.com'", html)

class HostSwitchTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='host_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)

    def test_player_host_switch(self):
        iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        res = self.client.get('/', HTTP_USER_AGENT=iphone_ua)
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        # uniform nocookie host on all devices (proven to play on desktop)
        self.assertIn('https://www.youtube-nocookie.com', html)
        self.assertIn("host: 'https://www.youtube-nocookie.com'", html)
        self.assertNotIn('ytHost', html)
        self.assertNotIn('widget_referrer', html)


class Fallback153NoApiTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='fallback_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)

    def test_onerror_153_fallback_to_noapi(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('onError', html)
        self.assertIn('playNextNoApi', html)
        self.assertIn('window._triedNoApi', html)
        self.assertIn('153 fallback to noapi', html)
        # fallback must be before breaker
        fallback_idx = html.find('window._triedNoApi')
        breaker_idx = html.find('consecutive153 >= 3')
        self.assertNotEqual(fallback_idx, -1)
        self.assertNotEqual(breaker_idx, -1)
        self.assertLess(fallback_idx, breaker_idx)
        # check pEl display reset and playNextNoApi call inside fallback
        self.assertIn("pEl.style.display = ''", html)

    def test_tried_noapi_reset_on_playing(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode()
        self.assertIn('YT.PlayerState.PLAYING', html)
        self.assertIn('window._triedNoApi = false', html)
        playing_idx = html.find('YT.PlayerState.PLAYING')
        reset_idx = html.find('window._triedNoApi = false')
        self.assertNotEqual(playing_idx, -1)
        self.assertNotEqual(reset_idx, -1)
        self.assertGreater(reset_idx, playing_idx)

class AudioApiTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def tearDown(self):
        from django.core.cache import cache
        cache.clear()

    def _mock_ydl(self, mock_ydl_class, info):
        from unittest.mock import MagicMock
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = info
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_class.return_value.__exit__.return_value = False
        return mock_ydl_instance

    def test_audio_success_returns_url_and_duration(self):
        from unittest.mock import patch
        from django.core.cache import cache
        with patch('music.views.YoutubeDL') as mock_ydl_class:
            self._mock_ydl(mock_ydl_class, {'url': 'https://example.com/audio.m4a', 'duration': 200})
            res = self.client.get('/api/audio/?id=ks7p6DA0dKk')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['audio_url'], 'https://example.com/audio.m4a')
        self.assertEqual(data['duration_sec'], 200)
        self.assertEqual(cache.get('aud:ks7p6DA0dKk')['audio_url'], 'https://example.com/audio.m4a')

    def test_audio_bad_id_400(self):
        res = self.client.get('/api/audio/?id=bad')
        self.assertEqual(res.status_code, 400)
        self.assertIn('id', res.json()['error'])

    def test_audio_all_fail_503(self):
        from unittest.mock import patch
        with patch('music.views.YoutubeDL', side_effect=Exception('bot blocked')):
            res = self.client.get('/api/audio/?id=ks7p6DA0dKk')
        self.assertEqual(res.status_code, 503)
        self.assertIn('ดึงเสียงไม่ได้', res.json()['error'])


class YouTubeAppFallbackTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='ytapp_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(self.staff_user)

    def test_player_has_youtube_app_fallback(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'youtube://watch?v=')
        self.assertContains(res, 'openInYouTubeApp')

class EmbedOkTests(TestCase):
    def _api_response(self, video_ids):
        import json as json_lib
        from unittest.mock import MagicMock
        payload = {
            'items': [
                {
                    'id': {'videoId': vid},
                    'snippet': {
                        'title': 'Test Song %s' % vid,
                        'channelTitle': 'Test Channel',
                        'thumbnails': {'medium': {'url': 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % vid}},
                    },
                }
                for vid in video_ids
            ]
        }
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json_lib.dumps(payload).encode('utf-8')
        return response

    def _oembed_ok_response(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.status = 200
        return response

    def test_oembed_401_filtered_out(self):
        import io
        import os
        import urllib.error
        from unittest.mock import patch
        from django.core.cache import cache
        from music.views import youtube_api_search
        cache.clear()
        video_id = 'AAA111BBB22'
        api_resp = self._api_response([video_id])
        oembed_401 = urllib.error.HTTPError(
            'https://www.youtube.com/oembed', 401,
            'Unauthorized', {}, io.BytesIO(b''),
        )
        def fake_urlopen(url_or_req, timeout=None):
            url = url_or_req.full_url if hasattr(url_or_req, 'full_url') else str(url_or_req)
            if 'www.googleapis.com' in url:
                return api_resp
            if 'youtube.com/oembed' in url:
                raise oembed_401
            raise AssertionError('unexpected url: %s' % url)
        env = {'YOUTUBE_API_KEYS': 'TESTKEY1', 'YOUTUBE_API_KEY': '', 'key': '', 'YOUTUBE_API_KEY_2': ''}
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen', side_effect=fake_urlopen):
                results = youtube_api_search('test song', 5)
        self.assertEqual([r['id'] for r in results], [])
        cache.clear()

    def test_oembed_200_kept(self):
        import os
        from unittest.mock import patch
        from django.core.cache import cache
        from music.views import youtube_api_search
        cache.clear()
        video_id = 'BBB222CCC33'
        api_resp = self._api_response([video_id])
        oembed_ok = self._oembed_ok_response()
        def fake_urlopen(url_or_req, timeout=None):
            url = url_or_req.full_url if hasattr(url_or_req, 'full_url') else str(url_or_req)
            if 'www.googleapis.com' in url:
                return api_resp
            if 'youtube.com/oembed' in url:
                return oembed_ok
            raise AssertionError('unexpected url: %s' % url)
        env = {'YOUTUBE_API_KEYS': 'TESTKEY1', 'YOUTUBE_API_KEY': '', 'key': '', 'YOUTUBE_API_KEY_2': ''}
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen', side_effect=fake_urlopen):
                results = youtube_api_search('test song', 5)
        self.assertEqual([r['id'] for r in results], [video_id])
        cache.clear()

    def test_oembed_urlerror_kept(self):
        import os
        import urllib.error
        from unittest.mock import patch
        from django.core.cache import cache
        from music.views import youtube_api_search
        cache.clear()
        video_id = 'CCC333DDD44'
        api_resp = self._api_response([video_id])
        def fake_urlopen(url_or_req, timeout=None):
            url = url_or_req.full_url if hasattr(url_or_req, 'full_url') else str(url_or_req)
            if 'www.googleapis.com' in url:
                return api_resp
            if 'youtube.com/oembed' in url:
                raise urllib.error.URLError('timed out')
            raise AssertionError('unexpected url: %s' % url)
        env = {'YOUTUBE_API_KEYS': 'TESTKEY1', 'YOUTUBE_API_KEY': '', 'key': '', 'YOUTUBE_API_KEY_2': ''}
        with patch.dict(os.environ, env):
            with patch('music.views.urllib.request.urlopen', side_effect=fake_urlopen):
                results = youtube_api_search('test song', 5)
        self.assertEqual([r['id'] for r in results], [video_id])
        cache.clear()


class NoStoreAndEmbed5Tests(TestCase):
    def test_player_no_store(self):
        self.client.force_login(User.objects.create_user(username='ns1', password='Testpass123!', is_staff=True))
        resp = self.client.get('/')
        self.assertIn('no-store', resp.get('Cache-Control', ''))
    def test_request_no_store(self):
        resp = self.client.get('/request/')
        self.assertIn('no-store', resp.get('Cache-Control', ''))
    def test_embed_section5_youtube_host(self):
        resp = self.client.get('/embed-test/')
        self.assertContains(resp, 'youtube.com/embed/ks7p6DA0dKk')

class SwCompatTests(TestCase):
    def test_sw_compat_hashed_url_serves_current_sw(self):
        res = self.client.get('/static/music/sw.deadbeef1234.js')
        self.assertEqual(res.status_code, 200)
        self.assertIn('javascript', res['Content-Type'])
        self.assertEqual(res['Cache-Control'], 'no-store')
        self.assertIn('yum-juke-v3', res.content.decode())

    def test_sw_source_has_no_document_precache(self):
        import os
        from django.conf import settings
        with open(os.path.join(settings.BASE_DIR, 'music', 'static', 'music', 'sw.js'), encoding='utf-8') as f:
            source = f.read()
        shell_lines = [line for line in source.splitlines() if 'SHELL' in line and '=' in line]
        self.assertTrue(shell_lines)
        shell_line = shell_lines[0]
        self.assertNotIn('"/"', shell_line)
        self.assertNotIn('"/request/"', shell_line)
        self.assertNotIn('"/request/"', source)

    def test_sw_source_bypasses_navigate(self):
        import os
        from django.conf import settings
        with open(os.path.join(settings.BASE_DIR, 'music', 'static', 'music', 'sw.js'), encoding='utf-8') as f:
            source = f.read()
        self.assertIn('request.mode === "navigate"', source)


class HitsEmbedFilterTests(TestCase):
    def test_hits_excludes_embed_blocked_spam_keeps_static(self):
        from unittest.mock import patch
        from django.core.cache import cache
        cache.clear()
        spam_id = 'SPAM1112223'
        spam_item = {
            'id': spam_id,
            'title': 'Longplay รวมเพลงฮิต 3 ชั่วโมงต่อเนื่อง',
            'channel': 'Spam Channel',
            'thumbnail': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % spam_id,
        }
        def fake_embed_ok(video_id):
            if video_id == spam_id:
                return False
            return True
        with patch('music.views.search_youtube', return_value=[spam_item]), \
             patch('music.views._is_embed_ok', side_effect=fake_embed_ok):
            cache.clear()
            res = self.client.get('/api/hits/?player=1')
            self.assertEqual(res.status_code, 200)
            results = res.json().get('results', [])
            ids = [r['id'] for r in results]
            self.assertNotIn(spam_id, ids)
            self.assertIn('ks7p6DA0dKk', ids)


class ClientLogTests(TestCase):
    def setUp(self):
        from .views import _rate_limit_store
        _rate_limit_store.clear()

    def test_post_saves_anon(self):
        from .models import ClientLog
        res = self.client.post('/api/clientlog/', data=json.dumps({'event': 'overlay_tap', 'detail': 'x'}), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('status'), 'ok')
        self.assertEqual(ClientLog.objects.filter(event='overlay_tap').count(), 1)

    def test_recent_403_anon(self):
        res = self.client.get('/api/clientlog/recent/')
        self.assertEqual(res.status_code, 403)

    def test_recent_200_staff(self):
        from .models import ClientLog
        staff = User.objects.create_user(username='clog_staff', password='Testpass123!', is_staff=True)
        self.client.force_login(staff)
        ClientLog.objects.create(event='beat', detail='q1')
        res = self.client.get('/api/clientlog/recent/?n=50')
        self.assertEqual(res.status_code, 200)
        self.assertIn('logs', res.json())
        self.assertGreaterEqual(len(res.json()['logs']), 1)

    def test_pruning_keeps_lte_500(self):
        from .models import ClientLog
        from .views import _rate_limit_store
        for i in range(500):
            ClientLog.objects.create(event='beat', detail=str(i))
        self.assertEqual(ClientLog.objects.count(), 500)
        _rate_limit_store.clear()
        res = self.client.post('/api/clientlog/', data=json.dumps({'event': 'beat', 'detail': 'new'}), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertLessEqual(ClientLog.objects.count(), 500)


class DatabaseSwitchTests(TestCase):
    def test_settings_source_has_database_url_switch(self):
        import os
        from django.conf import settings
        settings_path = os.path.join(settings.BASE_DIR, 'yum_jukebox', 'settings.py')
        with open(settings_path, 'r', encoding='utf-8') as f:
            source = f.read()
        self.assertIn('dj_database_url', source)
        self.assertIn('DATABASE_URL', source)

    def test_parse_postgres_url_in_isolation(self):
        try:
            import dj_database_url
        except ImportError:
            self.skipTest('dj_database_url not installed')
        parsed = dj_database_url.parse(
            'postgres://u:p@localhost:5432/db',
            conn_max_age=600,
            ssl_require=True,
        )
        self.assertIn('postgres', parsed.get('ENGINE', ''))
        self.assertEqual(parsed.get('NAME'), 'db')

