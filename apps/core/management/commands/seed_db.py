from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing data before seeding'
        )

    def handle(self, *args, **kwargs):
        if kwargs['force']:
            self.stdout.write('Clearing existing data...')
            User.objects.all().delete()
            self.stdout.write('Existing data cleared.')

        try:
            # Load fixtures
            fixtures = [
                'users.json',
                'tires.json',
                'warranties.json',
                'repair_requests.json',
                'technical_reports.json'
            ]
            
            for fixture in fixtures:
                try:
                    self.stdout.write(f'Loading fixture: {fixture}')
                    call_command('loaddata', fixture)
                    self.stdout.write(self.style.SUCCESS(f'Successfully loaded {fixture}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to load {fixture}: {str(e)}'))

            # Set different passwords for different users
            user_passwords = {
                'admin_user': 'admin123',
                'miner_user': 'miner123',
                'technical_user': 'technical123'
            }

            for username, password in user_passwords.items():
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Set password for {username}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Seeding failed: {str(e)}'))