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
                'production': {
                    'relative_path': 'settings.lms_production',
                },
            },
            'cms.djangoapp': {
                'production': {
                    'relative_path': 'settings.cms_production',
                },
            },
        },
        'signals_config': {
            'lms.djangoapp': {
                'relative_path': 'receivers',
                'receivers': [
                    {
                        'receiver_func_name': 'user_sync_to_idp',
                        'signal_path': 'django.db.models.signals.post_save',
                        'sender_path': 'django.contrib.auth.models.User',
                    },
                    {
                        'receiver_func_name': 'user_sync_to_idp',
                        'signal_path': 'django.db.models.signals.post_save',
                        'sender_path': 'student.models.UserProfile',
                    },
                ],
            },
            'cms.djangoapp': {
                'relative_path': 'receivers',
                'receivers': [
                    {
                        'receiver_func_name': 'user_sync_to_idp',
                        'signal_path': 'django.db.models.signals.post_save',
                        'sender_path': 'django.contrib.auth.models.User',
                    },
                    {
                        'receiver_func_name': 'user_sync_to_idp',
                        'signal_path': 'django.db.models.signals.post_save',
                        'sender_path': 'student.models.UserProfile',
                    },
                ],
            },

        },
    }
