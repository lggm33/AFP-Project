# Generated by Django 5.2.2 on 2025-06-12 03:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0002_emailqueue_emailprocessinglog_banktemplate_and_more'),
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BankSender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_email', models.EmailField(help_text='Unique bank sender email', max_length=254, unique=True)),
                ('sender_name', models.CharField(blank=True, help_text='Display name of the sender', max_length=255)),
                ('sender_domain', models.CharField(help_text='Domain for pattern matching', max_length=100)),
                ('is_verified', models.BooleanField(default=False, help_text='Verified by admin/community')),
                ('confidence_score', models.FloatField(default=0.8, help_text='Global confidence score for this sender')),
                ('total_emails_processed', models.IntegerField(default=0, help_text='Total emails processed across all users')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='senders', to='banking.bank')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_senders', to=settings.AUTH_USER_MODEL)),
                ('email_template', models.ForeignKey(blank=True, help_text='Template used to process emails from this sender', null=True, on_delete=django.db.models.deletion.SET_NULL, to='banking.banktemplate')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_senders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Bank Sender',
                'verbose_name_plural': 'Bank Senders',
                'ordering': ['-total_emails_processed', 'sender_email'],
            },
        ),
        migrations.CreateModel(
            name='UserBankSender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this sender is active for this user')),
                ('custom_confidence', models.FloatField(blank=True, help_text='User override confidence (overrides global)', null=True)),
                ('custom_name', models.CharField(blank=True, help_text="User's custom name for this sender", max_length=255)),
                ('emails_processed', models.IntegerField(default=0, help_text='Emails processed for this user from this sender')),
                ('last_email_at', models.DateTimeField(blank=True, help_text='Last email received from this sender', null=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True, help_text='User notes about this sender')),
                ('bank_sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_assignments', to='core.banksender')),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_senders', to='core.integration')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_bank_senders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Bank Sender',
                'verbose_name_plural': 'User Bank Senders',
                'ordering': ['-added_at'],
            },
        ),
        migrations.AddIndex(
            model_name='banksender',
            index=models.Index(fields=['sender_email'], name='core_bankse_sender__08910f_idx'),
        ),
        migrations.AddIndex(
            model_name='banksender',
            index=models.Index(fields=['sender_domain'], name='core_bankse_sender__bb42a1_idx'),
        ),
        migrations.AddIndex(
            model_name='banksender',
            index=models.Index(fields=['bank', 'is_verified'], name='core_bankse_bank_id_b41ed8_idx'),
        ),
        migrations.AddIndex(
            model_name='banksender',
            index=models.Index(fields=['total_emails_processed'], name='core_bankse_total_e_91773e_idx'),
        ),
        migrations.AddIndex(
            model_name='userbanksender',
            index=models.Index(fields=['user', 'integration', 'is_active'], name='core_userba_user_id_891b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='userbanksender',
            index=models.Index(fields=['bank_sender', 'is_active'], name='core_userba_bank_se_e86c7d_idx'),
        ),
        migrations.AddIndex(
            model_name='userbanksender',
            index=models.Index(fields=['last_email_at'], name='core_userba_last_em_de73b7_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userbanksender',
            unique_together={('user', 'integration', 'bank_sender')},
        ),
    ]
