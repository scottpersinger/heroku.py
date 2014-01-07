# -*- coding: utf-8 -*-

"""
heroku.core
~~~~~~~~~~~

This module provides the base entrypoint for heroku.py.
"""

from .api import Heroku
#from .mock import HerokuMock

def from_key(api_key, version=None):
    """Returns an authenticated Heroku instance, via API Key."""

    h = Heroku(version=version)

    # Login.
    h.authenticate(api_key)

    return h

def from_pass(username, password, version=None):
    """Returns an authenticated Heroku instance, via password."""

    key = get_key(username, password)
    return from_key(key, version=version)

def get_key(username, password):
    """Returns an API Key, fetched via password."""

    return Heroku().request_key(username, password)

def from_access_token(access_token, refresh_token = None, version=None):
    """Returns a Heroku instance authenticated from an Oauth access token."""
    h = Heroku(version=version)
    h.authenticate_oauth(access_token, refresh_token=refresh_token)
    return h