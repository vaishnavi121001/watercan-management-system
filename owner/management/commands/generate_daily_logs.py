# owner/management/commands/generate_daily_logs.py
from django.core.management.base import BaseCommand
from owner.utils import generate_daily_logs

class Command(BaseCommand):
    help = 'Generates daily delivery logs for assigned schedules'

    def handle(self, *args, **kwargs):
        generate_daily_logs()
        self.stdout.write(self.style.SUCCESS('Daily delivery logs generated successfully.'))
