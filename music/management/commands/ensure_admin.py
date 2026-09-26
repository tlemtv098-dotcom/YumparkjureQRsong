"""Create or repair the admin superuser and its Profile row.

This replaces the database access that used to live in
``MusicConfig.ready()``. Run it after ``migrate`` on every deploy:

    python manage.py ensure_admin

The command is idempotent, prints one line per change it makes and a summary
line, and never raises for an already-correct database.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from music.models import Profile

ADMIN_USERNAME = 'admin'
DEFAULT_PASSWORD = '11111111'


class Command(BaseCommand):
    help = 'Create or repair the admin superuser and its Profile row.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEFAULT_PASSWORD,
            help='Password to set on the admin user (default: %(default)s).',
        )

    def handle(self, *args, **options):
        password = options['password']
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
