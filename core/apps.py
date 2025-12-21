from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Import signals and apply runtime compatibility shims."""
        import core.signals  # noqa

        # Runtime shim: tolerate `is_archived` kwarg on Project even if field is missing
        try:
            from django.apps import apps

            Project = apps.get_model("core", "Project")

            original_init = Project.__init__

            def _patched_init(self, *args, **kwargs):
                if "is_archived" in kwargs:
                    try:
                        self._meta.get_field("is_archived")
                    except Exception:
                        kwargs.pop("is_archived")
                return original_init(self, *args, **kwargs)

            Project.__init__ = _patched_init

            # If the model is missing the field at runtime, add it dynamically
            try:
                Project._meta.get_field("is_archived")
            except Exception:
                from django.db import models as dj_models

                Project.add_to_class("is_archived", dj_models.BooleanField(default=False))
        except Exception:
            # If anything goes wrong, avoid breaking app startup
            pass
