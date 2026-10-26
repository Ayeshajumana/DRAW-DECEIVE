from django.core.management.base import BaseCommand
from words.services import seed_default_words

class Command(BaseCommand):
    help = 'Seeds initial curated words dataset for DRAW & DECEIVE'

    def handle(self, *args, **options):
        count = seed_default_words()
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} words!'))
