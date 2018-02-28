# -*- coding:utf-8 -*-

def build_conf_dict(name, bid, qualnames, message, level='MEDIUM'):
    """Build and return a blacklist configuration dict."""

    return {'name': name, 'id': bid, 'message': message,
            'qualnames': qualnames, 'level': level}
