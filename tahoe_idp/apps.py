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
            }
        },
    }

    def ready(self):
        logger.debug("Tahoe IdP plugin is ready.")
