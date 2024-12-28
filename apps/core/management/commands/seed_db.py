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

            # Set different passwords and verify emails for different users
            user_data = {
                'admin_user': {'password': 'admin123', 'email_verified': True},
                'miner_user': {'password': 'miner123', 'email_verified': True},
                'technical_user': {'password': 'technical123', 'email_verified': True}
            }

            for username, data in user_data.items():
                try:
                    user = User.objects.get(username=username)
                    user.set_password(data['password'])
                    user.email_verified = data['email_verified']
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated user {username}'))
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User {username} not found'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Seeding failed: {str(e)}'))