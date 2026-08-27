import json
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
        self.assertContains(response, 'toggleMute')
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
    def test_clear_queue_empties_songs(self):
        from .models import SongQueue
        SongQueue.objects.create(title='A', video_id='a', thumbnail='', channel='', requested_by='x')
        SongQueue.objects.create(title='B', video_id='b', thumbnail='', channel='', requested_by='y')
        response = self.client.post('/api/clear/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SongQueue.objects.count(), 0)


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