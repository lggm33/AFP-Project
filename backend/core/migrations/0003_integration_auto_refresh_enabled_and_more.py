# Generated by Django 5.2.2 on 2025-06-13 00:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_banksender_userbanksender_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='auto_refresh_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='last_refresh_attempt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='oauth_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='oauth_token_refreshed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='oauth_token_status',
            field=models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('revoked', 'Revoked'), ('error', 'Error')], default='active', max_length=20),
        ),
        migrations.AddField(
            model_name='integration',
            name='refresh_error_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='integration',
            name='refresh_error_message',
            field=models.TextField(blank=True),
        ),
        migrations.AddIndex(
            model_name='integration',
            index=models.Index(fields=['oauth_token_status'], name='core_integr_oauth_t_583fae_idx'),
        ),
        migrations.AddIndex(
            model_name='integration',
            index=models.Index(fields=['oauth_token_expires_at'], name='core_integr_oauth_t_420b62_idx'),
        ),
        migrations.AddIndex(
            model_name='integration',
            index=models.Index(fields=['last_refresh_attempt'], name='core_integr_last_re_0832cd_idx'),
        ),
    ]
