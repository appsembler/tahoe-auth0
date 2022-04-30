import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TahoeIdpConfig(AppConfig):
    name = "tahoe_idp"
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "tahoe_idp",
                "regex": "^tahoe-idp/api/v1/",
            },
            "cms.djangoapp": {
                # TODO: Only include `path('login/', Login.as_view(), name='login'),` to avoid including signups
                "namespace": "magiclink",
                "app_name": "magiclink",
                "regex": "^auth_link/",
            },
        },
        "settings_config": {
            "lms.djangoapp": {
                "common": {
                    "relative_path": "settings.common",
                },
            },
            "cms.djangoapp": {
                "common": {
                    "relative_path": "settings.cms",
                },
            },
        },
    }

    def ready(self):
        logger.debug("Tahoe IdP plugin is ready.")
