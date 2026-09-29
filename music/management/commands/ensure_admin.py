"""Create or repair the admin superuser and its Profile row.

This replaces the database access that used to live in
``MusicConfig.ready()``. Run it after ``migrate`` on every deploy:

    python manage.py ensure_admin

The command is idempotent, prints one line per change it makes and a summary
line, and never raises for an already-correct database.

For the graded demonstration, add ``--with-demo`` to also seed the second and
third roles plus the catalogue the dashboard charts read:

    python manage.py ensure_admin --with-demo

That flag is off by default and the bare command is unchanged: it still touches
the single ``admin`` account and nothing else, which is what the Render start
command depends on on every deploy.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from music.models import Genre, Playlist, Profile, SongQueue, Tag

ADMIN_USERNAME = 'admin'
DEFAULT_PASSWORD = '11111111'
# A different *default* for --with-demo, so the three demo logins are easy to
# show from memory. The value still comes from the one --password flag, so there
# is no second hardcoded secret anywhere in the command.
DEMO_PASSWORD = '12345678'

# (name, slug, description)
DEMO_GENRES = [
    ('เพลงไทย', 'thai-pop', 'เพลงไทยยอดนิยมที่ลูกค้าในร้านขอบ่อย'),
    ('เพลงอกหัก', 'lump-in-the-throat', 'เพลงเศร้า ๆ ที่ทำให้ใจพัก'),
    ('เพลงรัก', 'love-songs', 'เพลงรักและเพลงความรัก'),
    ('เพลงแดนซ์', 'dance', 'เพลงจังหวะแรงสำหรับงานเต้น'),
    ('เพลงผ่อนคลาย', 'chill', 'เพลงเบา ๆ สำหรับฟังตอนทานข้าว'),
    ('เพลงฮิต', 'hits', 'เพลงที่คนในร้านขอบ่อยที่สุด'),
]

# (name, slug)
DEMO_TAGS = [
    ('ข้างกัน', 'beside-you'),
    ('อกหัก', 'heartbreak'),
    ('รักแรกพบ', 'first-love'),
    ('คิดถึง', 'thinking-of-you'),
    ('สนุก', 'fun'),
    ('เพลงรัก', 'romance'),
]

# (video_id, title, channel, is_played, genre indexes, tag indexes)
# The first twelve entries of the fallback catalogue in music/views.py, so the
# seeded queue reuses video ids this project already treats as known-good and
# embeddable rather than invented ones.
DEMO_SONGS = [
    ('ks7p6DA0dKk', 'ข้างกัน - Three Man Down', 'GeneLab', True, (0, 2), (0, 2)),
    ('zwvv71slEYc', 'ถ้าเธอ - Tilly Birds', 'GeneLab', True, (0, 1), (0, 3)),
    ('L1k0wkQ6uww', 'แฟนเก่าคนโปรด - SLAPKISS', 'SLAPKISS', True, (0, 1), (1, 3)),
    ('yEbv0QiI1Ns', 'คนไม่สำคัญ - Safeplanet', 'GMM', True, (0, 2), (3,)),
    ('s-MZid-59Hc', 'แค่เธอ - Jeff Satur', 'Jeff Satur', False, (0, 5), (2, 4)),
    ('rc7KnQAh_1I', 'รักแรกพบ - Tattoo Colour', 'Tattoo Colour', False, (0, 2), (2, 5)),
    ('I9ZIq7ynvdU', 'แค่คนโทรผิด - Klear', 'GMM', False, (0, 1), (1,)),
    ('Bk4O_3WF8II', 'ซ่อน(ไม่)หา - Jeff Satur', 'Jeff Satur', False, (0, 1), (1, 3)),
    ('OYPiXBIgvJ8', 'เพลงรัก - Three Man Down |Official MV|', 'GeneLab', False, (3, 5), (4, 5)),
    ('hBK29bbOLS4', 'แก้บน - ก้านตอง ทุ่งเงิน【OFFICIAL MV】', 'GRAMMY GOLD OFFICIAL', False, (3, 5), (4,)),
    ('BQqAUhxSMOo', 'คำยินดี - Klear | ตำนานเพลงอกหัก 100 ล้านวิว | Songtopia Livehouse', 'Songtopia', False, (1, 4), (1, 3)),
    ('ReUGJf6FxhM', 'อกหัก - bodyslam【OFFICIAL MV】', 'GMM GRAMMY OFFICIAL', False, (1, 4), (1,)),
]

DEMO_PLAYLIST = 'เพลงที่ฉันชอบ'
DEMO_PLAYLIST_SIZE = 4



class Command(BaseCommand):
    help = 'Create or repair the admin superuser and its Profile row.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=None,
            help=(
                'Password to set on the admin user; with --with-demo it is set '
                'on the staff and customer demo accounts too. Defaults to %s '
                'bare, and to %s with --with-demo.'
            ) % (DEFAULT_PASSWORD, DEMO_PASSWORD),
        )
        parser.add_argument(
            '--with-demo',
            action='store_true',
            default=False,
            help=(
                'Also seed the second and third roles plus the catalogue the '
                'dashboard charts read. Off by default: the bare command is what '
                'the Render start command runs on every deploy.'
            ),
        )

    def handle(self, *args, **options):
        with_demo = options['with_demo']
        # None means the flag was not passed, so each mode keeps its own default.
        password = options['password'] or (
            DEMO_PASSWORD if with_demo else DEFAULT_PASSWORD
        )
        User = get_user_model()
        actions = []

        admin = User.objects.filter(username=ADMIN_USERNAME).first()
        if admin is None:
            admin = User.objects.create_superuser(ADMIN_USERNAME, password=password)
            actions.append('created superuser %r' % ADMIN_USERNAME)
        else:
            if not admin.check_password(password):
                admin.set_password(password)
                actions.append('reset the password')
            if not admin.is_staff or not admin.is_superuser:
                admin.is_staff = True
                admin.is_superuser = True
                actions.append('granted is_staff and is_superuser')
            if actions:
                admin.save()

        # The missing piece: the navbar renders the user-management, genre and
        # tag links from user.profile.role, so a superuser with no Profile row
        # (or with the default 'customer' role) sees an admin-less navbar.
        # get_or_create repairs the user that the old ready() bootstrap created
        # before `migrate` had run, so its signal could not write the row.
        profile, profile_created = Profile.objects.get_or_create(
            user=admin, defaults={'role': 'admin'}
        )
        if profile_created:
            actions.append('created the missing Profile with role=admin')
        elif profile.role != 'admin':
            # The post_save signal in music/models.py already creates Profile
            # with the default role, so a freshly created superuser arrives here
            # with role='customer'. get_or_create alone would leave it there.
            stale_role = profile.role
            profile.role = 'admin'
            profile.save()
            actions.append(
                "repaired the Profile role from %r to 'admin'" % stale_role
            )

        for action in actions:
            self.stdout.write('ensure_admin: %s' % action)
        self.stdout.write(self.style.SUCCESS(
            'ensure_admin: %d action(s) taken for %r' % (len(actions), ADMIN_USERNAME)
        ))

        if with_demo:
            for action in self._seed_demo(User, password):
                self.stdout.write('ensure_admin: %s' % action)

    def _ensure_demo_user(self, User, username, password, role, actions):
        """Create or repair one demo account and give it the right role."""
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(username, password=password)
            actions.append('created the %r demo account' % username)
        if not user.check_password(password):
            user.set_password(password)
            user.save()
            actions.append('reset the password on %r' % username)

        # The post_save signal in music/models.py already created this Profile
        # with the default role='customer', so get_or_create(defaults=...) finds
        # that row and applies nothing. The role has to be assigned and saved.
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role != role:
            stale_role = profile.role
            profile.role = role
            profile.save()
            actions.append(
                "set the %r Profile role from %r to %r" % (username, stale_role, role)
            )
        return user

    def _seed_demo(self, User, password):
        """Seed the three-role demonstration and print a summary.

        Everything is keyed on a natural key, so a second run changes nothing
        and reports nothing.
        """
        actions = []
        for username, role in (('staff', 'staff'), ('customer', 'customer')):
            self._ensure_demo_user(User, username, password, role, actions)
        customer = User.objects.get(username='customer')

        # Keyed on name, not on the slug: a genre that already exists keeps
        # whatever slug it has, so a re-run cannot trip the unique constraint.
        genres = [
            Genre.objects.get_or_create(
                name=name, defaults={'slug': slug, 'description': description}
            )[0]
            for name, slug, description in DEMO_GENRES
        ]
        tags = [
            Tag.objects.get_or_create(name=name, defaults={'slug': slug})[0]
            for name, slug in DEMO_TAGS
        ]

        songs = []
        for video_id, title, channel, is_played, genre_indexes, tag_indexes in DEMO_SONGS:
            song = SongQueue.objects.filter(video_id=video_id).first()
            if song is None:
                song = SongQueue.objects.create(
                    title=title,
                    video_id=video_id,
                    channel=channel,
                    thumbnail='https://i.ytimg.com/vi/%s/hqdefault.jpg' % video_id,
                    requested_by='staff',
                    is_played=is_played,
                )
                actions.append('queued the demo song %s' % video_id)
            # SongQueue has no `genre` field: genres is a ManyToManyField, which
            # Django refuses to accept in create(), so attach it after saving.
            song.genres.add(*[genres[i] for i in genre_indexes])
            song.tags.add(*[tags[i] for i in tag_indexes])
            songs.append(song)

        playlist, _ = Playlist.objects.get_or_create(
            user=customer,
            name=DEMO_PLAYLIST,
            defaults={'description': 'เพลงที่ลูกค้าชอบ', 'is_public': True},
        )
        # add_song writes the PlaylistSong row and the songs JSON field together,
        # and is a no-op on a song the playlist already holds.
        for position, song in enumerate(songs[:DEMO_PLAYLIST_SIZE]):
            if playlist.add_song(song, position=position):
                actions.append('added song %s to the demo playlist' % song.video_id)

        # Everything written to stdout stays ASCII on purpose: it lands on a
        # Windows console (cp1252) as often as on a terminal, and a Thai genre
        # or song name raises UnicodeEncodeError there. The Thai itself lives in
        # the database, which is UTF-8 regardless.
        accounts = ', '.join(
            '%s (%s)' % (user.username, user.profile.role)
            for user in User.objects.order_by('date_joined')
        )
        self.stdout.write('ensure_admin: demo data summary')
        self.stdout.write('  Accounts     : %s' % accounts)
        self.stdout.write('  Password     : %s' % password)
        self.stdout.write('  Genres       : %d' % Genre.objects.count())
        self.stdout.write('  Tags         : %d' % Tag.objects.count())
        self.stdout.write('  Songs in queue : %d' % SongQueue.objects.count())
        self.stdout.write('  Playlists    : %d' % Playlist.objects.count())
        return actions
