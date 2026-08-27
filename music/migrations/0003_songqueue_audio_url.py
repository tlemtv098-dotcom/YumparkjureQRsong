from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('music', '0002_songqueue_client_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='songqueue',
            name='audio_url',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
    ]
