from django.apps import AppConfig


class MusicConfig(AppConfig):
    name = 'music'

    def ready(self):
        # Create persistent admin user (11111111) if not exists - survives Render SQLite wipe via re-create on startup
        try:
            from django.contrib.auth import get_user_model
            from django.db.utils import OperationalError, ProgrammingError
            User = get_user_model()
            # Only run if table exists
            if not User.objects.filter(username='admin').exists():
                try:
                    User.objects.create_user('admin', password='11111111', is_staff=True, is_superuser=True)
                    print("Created persistent admin/admin")
                except Exception as e:
                    print(f"admin create failed: {e}")
            else:
                # Ensure password is 11111111 and is_staff
                try:
                    u = User.objects.get(username='admin')
                    if not u.check_password('11111111'):
                        u.set_password('11111111')
                        u.is_staff = True
                        u.is_superuser = True
                        u.save()
                        print("Reset admin password to 11111111")
                except Exception as e:
                    print(f"admin reset failed: {e}")
        except (OperationalError, ProgrammingError) as e:
            # DB not ready yet (migrations not run)
            pass
        except Exception as e:
            print(f"MusicConfig ready error: {e}")
