import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TahoeAuth0Config(AppConfig):
    name = "tahoe_auth0"
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "tahoe_auth0",
                "regex": "^tahoeauth0/api/v1/",
            }
        },
    }

    def ready(self):
        logger.debug("Tahoe Auth0 plugin is ready.")
