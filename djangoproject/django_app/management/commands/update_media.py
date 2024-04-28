from django.conf import settings
from django.core.management.base import BaseCommand
import os
from moviepy.editor import VideoFileClip, AudioFileClip
from django_app.models import Media
from django.utils import timezone

class Command(BaseCommand):
    help = 'Automatically scans the media folder and updates the media database'

    def add_arguments(self, parser):
        # Добавление аргумента folder_path, который может быть передан в команду
        parser.add_argument('folder_path', type=str, help='Path to the media folder')
        
        
    def handle(self, *args, **options):
        # Получение пути к папке из аргументов
        folder_path = options['folder_path']
        self.update_media_from_folder(folder_path)  # Вызов функции с нужным путем

    def update_media_from_folder(self, folder_path):
        existing_media_titles = Media.objects.all().values_list('title', flat=True)
        existing_media = {media.title: media for media in Media.objects.all()}
        actual_filenames = set(os.listdir(folder_path))

        # Update status for missing files
        for title, media in existing_media.items():
            if title not in actual_filenames:
                media.status = 'Отсутствует'
                media.save()

        # Add new media files to the DB
        for filename in actual_filenames:
            if filename.endswith((".mp4", ".avi", ".mp3")) and filename not in existing_media_titles:
                file_path = os.path.join(folder_path, filename)
                try:
                    clip = VideoFileClip(file_path) if filename.endswith((".mp4", ".avi")) else AudioFileClip(file_path)
                    duration_seconds = int(clip.duration)
                    duration_formatted = f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600 // 60):02d}:{duration_seconds % 60:02d}"
                    clip.close()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing file {filename}: {e}'))
                    continue

                Media.objects.create(
                    title=filename,
                    file=filename,  # file будет автоматически префиксирован upload_to параметром в модели Media
                    created_at=timezone.now(),
                    duration=duration_formatted,
                    tags="",
                    status='Активен'
                )

        self.stdout.write(self.style.SUCCESS('Successfully updated media files'))
