# -*- coding: utf-8 -*-

"""
heroku.api
~~~~~~~~~~

This module provides the basic API interface for Heroku.
"""

from .compat import json
from .helpers import is_collection, patch_models_version3
from .models import *
from .structures import KeyedListResource
from heroku.models import Feature
from requests.exceptions import HTTPError
import requests

HEROKU_URL = 'https://api.heroku.com'


class HerokuCore(object):
    """The core Heroku class."""
    def __init__(self, session=None, version=None):
        super(HerokuCore, self).__init__()
        if session is None:
            session = requests.session()

        #: The User's API Key.
        self._api_key = None
        self._api_key_verified = None
        self._heroku_url = HEROKU_URL
        self._session = session
        session.trust_env = False
        self._version = version

        # We only want JSON back.
        if version is not None:
            if version == 3:
                patch_models_version3()
            self._session.headers.update({'Accept': 'application/vnd.heroku+json; version=%d' % version})
        else:
            self._session.headers.update({'Accept': 'application/json'})

    def __repr__(self):
        return '<heroku-core at 0x%x>' % (id(self))

    def authenticate(self, api_key):
        """Logs user into Heroku with given api_key."""
        self._api_key = api_key

        # Attach auth to session.
        self._session.auth = ('', self._api_key)

        return self._verify_api_key()

    def authenticate_oauth(self, access_token, refresh_token = None, oauth_secret=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.oauth_secret = oauth_secret
        self._session.headers['Authorization'] = "Bearer %s" % self.access_token

    def refresh_access_token(self):
        """Call this if you get a 401 and want to retrieve a new access token"""
        if hasattr(self, 'refresh_token') and hasattr(self, 'oauth_secret'):
            r = self._session.request('POST', self._heroku_url + '/oauth/token',
                                            {'grant_type':'refresh_token',
                                             'refresh_token':self.refresh_token,
                                             'client_secret':self.oauth_secret})
            if r.status_code == 200:
                j = r.json()
                self.access_token = j['access_token']
                self.refresh_token = j['refresh_token']
                return self.access_token, self.refresh_token
            else:
                return None
        else:
            return None

    def request_key(self, username, password):
        r = self._http_resource(
            method='POST',
            resource=('login'),
            data={'username': username, 'password': password}
        )
        r.raise_for_status()

        return json.loads(r.content).get('api_key')

    @property
    def is_authenticated(self):
        if self._api_key_verified is None:
            return self._verify_api_key()
        else:
            return self._api_key_verified

    def _verify_api_key(self):
        r = self._session.get(self._url_for('apps'))

        self._api_key_verified = True if r.ok else False

        return self._api_key_verified

    def _url_for(self, *args):
        args = map(str, args)
        return '/'.join([self._heroku_url] + list(args))

    @staticmethod
    def _resource_serialize(o):
        """Returns JSON serialization of given object."""
        return json.dumps(o)

    @staticmethod
    def _resource_deserialize(s):
        """Returns dict deserialization of a given JSON string."""

        try:
            return json.loads(s)
        except ValueError:
            raise ResponseError('The API Response was not valid.')

    def _http_resource(self, method, resource, params=None, data=None):
        """Makes an HTTP request."""

        if not is_collection(resource):
            resource = [resource]

        url = self._url_for(*resource)
        r = self._session.request(method, url, params=params, data=data)

        if r.status_code == 422:
            http_error = HTTPError('%s Client Error: %s' % (r.status_code, r.content))
            http_error.response = r
            raise http_error
        
        r.raise_for_status()

        return r

    def _get_resource(self, resource, obj, params=None, **kwargs):
        """Returns a mapped object from an HTTP resource."""
        r = self._http_resource('GET', resource, params=params)
        item = self._resource_deserialize(r.content)

        return obj.new_from_dict(item, h=self, **kwargs)

    def _get_resources(self, resource, obj, params=None, map=None, **kwargs):
        """Returns a list of mapped objects from an HTTP resource."""
        r = self._http_resource('GET', resource, params=params)
        d_items = self._resource_deserialize(r.content)

        items =  [obj.new_from_dict(item, h=self, **kwargs) for item in d_items]

        if map is None:
            map = KeyedListResource

        list_resource = map(items=items)
        list_resource._h = self
        list_resource._obj = obj
        list_resource._kwargs = kwargs

        return list_resource


class Heroku(HerokuCore):
    """The main Heroku class."""

    def __init__(self, session=None, version=None):
        super(Heroku, self).__init__(session=session, version=version)

    def __repr__(self):
        return '<heroku-client at 0x%x>' % (id(self))

    @property
    def addons(self):
        return self._get_resources(('addons'), Addon)

    @property
    def apps(self):
        return self._get_resources(('apps'), App)

    @property
    def keys(self):
        return self._get_resources(('user', 'keys'), Key, map=SSHKeyListResource)
    
    @property
    def labs(self):
        return self._get_resources(('features'), Feature, map=filtered_key_list_resource_factory(lambda obj: obj.kind == 'user'))
        



class ResponseError(ValueError):
    """The API Response was unexpected."""
