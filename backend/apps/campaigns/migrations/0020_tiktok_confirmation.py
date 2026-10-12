from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('campaigns', '0019_tiktok_upload')]
    operations = [
        migrations.AddField(model_name='tiktokupload', name='confirmation_source',
                            field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name='tiktokupload', name='published_at',
                            field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(name='TikTokWebhookReceipt', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('digest', models.CharField(max_length=64, unique=True)),
            ('event', models.CharField(max_length=64)),
            ('received_at', models.DateTimeField(auto_now_add=True)),
            ('upload', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='campaigns.tiktokupload')),
        ]),
    ]
