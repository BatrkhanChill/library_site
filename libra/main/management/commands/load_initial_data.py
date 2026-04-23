from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Load initial fixture data only if the database is empty'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            self.stdout.write('Database already has data — skipping loaddata.')
            return

        self.stdout.write('Database is empty — loading fixture data...')
        from django.core.management import call_command
        call_command('loaddata', 'data.json', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Fixture data loaded successfully.'))
