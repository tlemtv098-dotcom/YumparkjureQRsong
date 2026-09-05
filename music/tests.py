import json
from django.conf import settings
from django.test import TestCase

LOGO = '/static/music/img/logo.jpg'


class PlayerPageTests(TestCase):
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
        self.assertContains(response, 'id=\"result-panel\"')
        self.assertContains(response, 'mySongId')
        self.assertContains(response, 'updateMyStatus')
        self.assertContains(response, 'คิวของคุณ')
        self.assertNotContains(response, 'กำลังเล่นเพลงนี้เลย')
        self.assertNotContains(response, '6000')

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
        self.assertContains(response, 'genre-tab')


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
        client.get('/')
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
    def test_500_template_exists(self):
        import os
        from django.conf import settings
        self.assertTrue(os.path.exists(os.path.join(settings.BASE_DIR, 'music', 'templates', '500.html')))


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
            res = self.client.get('/api/hits/')
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
    def test_only_sound_overlay_exists(self):
        res = self.client.get('/')
        content = res.content.decode()
        self.assertIn('id="sound-overlay"', content)
        self.assertNotIn('id="queue-overlay"', content)


class SearchFastFallbackRegressionTests(TestCase):
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
                       side_effect=[quota_error, self._success_response()]) as mock_urlopen:
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
                                    self._success_response()]) as mock_urlopen:
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

    def test_clear_blocked_deletes_only_fallback_ids(self):
        from .models import BlockedVideo
        BlockedVideo.objects.create(video_id='ks7p6DA0dKk', reason='Error 153')
        BlockedVideo.objects.create(video_id='ZZZZZZZZZZZ', reason='Error 153')
        # without token -> 403, rows untouched
        res = self.client.post('/api/block/clear/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(BlockedVideo.objects.filter(video_id='ks7p6DA0dKk').count(), 1)
        self.assertEqual(BlockedVideo.objects.filter(video_id='ZZZZZZZZZZZ').count(), 1)
        # owner clears only FALLBACK_IDS rows
        res = self.client.post('/api/block/clear/', headers={'X-Player-Token': settings.PLAYER_TOKEN})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(BlockedVideo.objects.filter(video_id='ks7p6DA0dKk').count(), 0)
        self.assertEqual(BlockedVideo.objects.filter(video_id='ZZZZZZZZZZZ').count(), 1)

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