from django.apps import AppConfig


class JoetexConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "joetex"

    def ready(self):
        import joetex.signals  # Make sure this is correct
