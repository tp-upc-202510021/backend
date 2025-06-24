from django.apps import AppConfig
from django.db.models.signals import post_migrate


class BadgesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "badges"

    def ready(self):
        from .signals import create_default_badges 

        post_migrate.connect(
            create_default_badges,
            sender=self,
            dispatch_uid="badges.create_default_badges",
        )
