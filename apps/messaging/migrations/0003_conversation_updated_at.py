import django.utils.timezone
from django.db import migrations, models
from django.db.models import F


def copy_created_to_updated(apps, schema_editor):
    Conversation = apps.get_model("messaging", "Conversation")
    Conversation.objects.all().update(updated_at=F("created_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0002_conversation_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="updated_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RunPython(copy_created_to_updated, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="conversation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
