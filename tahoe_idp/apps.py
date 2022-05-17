import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TahoeIdpConfig(AppConfig):
    name = "tahoe_idp"
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {}
