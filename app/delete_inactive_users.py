from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete users who are not active for more than 3 days'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(days=3)
        users_to_delete = User.objects.filter(is_active=False, date_joined__lt=threshold)
        users_to_delete.delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted inactive users'))
