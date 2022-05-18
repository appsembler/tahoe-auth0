from tahoe_idp.magiclink_utils import get_url_path


def test_get_url_path_with_name():
    url_name = 'no_login'
    url = get_url_path(url_name)
    assert url == '/no-login/'


def test_get_url_path_with_path():
    url_name = '/test/'
    url = get_url_path(url_name)
    assert url == '/test/'
