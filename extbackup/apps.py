from django.apps import AppConfig


class ExtbackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extbackup'

    def ready(self):
        import extbackup.signals  # noqa
