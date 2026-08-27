# Generated
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('music', '0003_songqueue_audio_url')]
    operations = [migrations.CreateModel(name='BlockedVideo', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('video_id', models.CharField(max_length=50, unique=True)), ('reason', models.CharField(default='Error 153', max_length=100)), ('created_at', models.DateTimeField(auto_now_add=True))])]
