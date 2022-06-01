from django.apps import AppConfig


class TahoeIdpConfig(AppConfig):
    name = "tahoe_idp"
    default_auto_field = "django.db.models.BigAutoField"

    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'tahoe_idp',
                'app_name': 'tahoe_idp',
            },
            'cms.djangoapp': {
                'namespace': 'tahoe_idp',
                'app_name': 'tahoe_idp',
            }
        },

        'settings_config': {
            'lms.djangoapp': {
                'common': {
                    'relative_path': 'settings.common',
                },
            },
            'cms.djangoapp': {
                'common': {
                    'relative_path': 'settings.common',
                },
            },
        },
    }
