from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.accounts.models import User
from django.db import connection

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
            # Get list of all tables
            tables = connection.introspection.table_names()
            excluded_tables = ['django_migrations', 'django_content_type', 'django_session']
            
            with connection.cursor() as cursor:
                # Disable foreign key checks
                if connection.vendor == 'postgresql':
                    cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
                
                # Clear each table
                for table in tables:
                    if table not in excluded_tables:
                        self.stdout.write(f'Clearing table: {table}')
                        cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
                
                # Re-enable foreign key checks
                if connection.vendor == 'postgresql':
                    cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')
            
            self.stdout.write('Existing data cleared.')

        try:
            # Load fixtures in order of dependencies
            fixtures = [
                'users.json',           # Base users
                'categories.json',      # Tire categories
                'tire_models.json',     # Tire models (depends on categories)
                'tires.json',          # Tires (depends on models and users)
                'warranties.json',      # Warranties (depends on tires)
                'repair_requests.json', # Repair requests (depends on tires)
                'technical_reports.json', # Tech reports (depends on tires)
                'training_categories.json', # Training categories
                'trainings.json',      # Training content
                'training_requests.json' # Training requests
            ]

            for fixture in fixtures:
                try:
                    self.stdout.write(f'Loading fixture: {fixture}')
                    call_command('loaddata', fixture)
                    self.stdout.write(self.style.SUCCESS(f'Successfully loaded {fixture}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to load {fixture}: {str(e)}'))

            # Set passwords for users using phone numbers
            user_passwords = {
                '09121111111': 'admin123',
                '09122222222': 'miner123',
                '09123333333': 'miner123',
                '09124444444': 'technical123'
            }

            for phone, password in user_passwords.items():
                try:
                    user = User.objects.get(phone=phone)
                    user.set_password(password)
                    user.save()
                    
                    # Verify password was set correctly
                    if user.check_password(password):
                        self.stdout.write(self.style.SUCCESS(
                            f'Successfully set and verified password for user {phone}'
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f'Password verification failed for user {phone}'
                        ))
                        
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User with phone {phone} not found'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Seeding failed: {str(e)}'))