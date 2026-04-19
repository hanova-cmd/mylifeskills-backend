from django.db import migrations

def create_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', 'ПОСЛЕДНЯЯ_МИГРАЦИЯ'),
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]