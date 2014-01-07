import yaml
import pdb
import binascii
import os
from os.path import expanduser
import os.path
import json

from .api import Heroku
from .structures import KeyedListResource
from .models import Addon, App
from .helpers import is_collection


MOCK_DATA = """
apps:
  - id: 5e83558e-1d1b-4601-855a-353cab92d5f8
    name: sharp-sword-128
    created_at: "2012-10-11T20:23:44Z"
    addons:
      - id: 383838-383838
        name: herokuconnect-basic
  - id: 5838383s-3939-3833-1891-393833003333
    name: test-app-25
    created_at: "2012-10-11T20:23:44Z"
"""

class HerokuMock(Heroku):
    data = yaml.load(MOCK_DATA)
    DATA_FILE_NAME = expanduser("~/heroku_mock.yml")

    def __init__(self, version=None):
        self._addon_callable = {}
        try:
            HerokuMock.data = yaml.load(open(HerokuMock.DATA_FILE_NAME).read())
        except IOError:
            pass

        return super(HerokuMock, self).__init__(version=version)

    def save_mock_data(self):
        with open(HerokuMock.DATA_FILE_NAME, "w") as f:
            f.write(yaml.dump(HerokuMock.data))

    def set_addon_configure(self, addon_name, callable):
        self._addon_callable[addon_name] = callable

    def _matches(self, target, key):
        return target.get('id',None) == key or target.get('name',None) == key

    def _find_resource(self, resource):
        top = HerokuMock.data
        for elt in resource:
            if isinstance(top, (list, tuple)):
                match = None
                for child in top:
                    if self._matches(child, elt):
                        match = child
                        break
                top = match
                if not top:
                    raise KeyError(child)
            else:
                if elt in top:
                    top = top[elt]
                else:
                    empty = []
                    top[elt] = empty
                    top = empty
        return top

    def _get_resource(self, resource, obj, params=None, **kwargs):
        data = HerokuMock.data
        if type(resource) is tuple:
            data = self._find_resource(list(resource)[0:-1])
            resource = list(resource)[-1]

        result = None
        try:    
            return obj.new_from_dict(data[resource], h=self, **kwargs)
        except KeyError:
            return obj.new_from_dict({}, h=self, **kwargs)


    def _get_resources(self, resource, obj, params=None, map=None, **kwargs):
        #print "_get_resources (self: %s), resource: %s, obj: %s" % (str(self), str(resource), str(obj))

        data = HerokuMock.data

        if type(resource) is tuple:
            data = self._find_resource(list(resource)[0:-1])
            resource = list(resource)[-1]

        if resource in data:
            source = data[resource]
        else:
            source = []

        if isinstance(source, list):
            items = [obj.new_from_dict(item, h=self, **kwargs) for item in source]
        else:
            items = [obj.new_from_dict(source)]
        
        if map is None:
            map = KeyedListResource

        list_resource = map(items=items)
        list_resource._h = self
        list_resource._obj = obj
        list_resource._kwargs = kwargs

        return list_resource

    def _http_resource(self, method, resource, params=None, data=None):
        resource_path = list(resource)
        if len(resource_path) > 1:
            child = resource_path.pop()
        else:
            try:
                child = data["app[name]"]
            except KeyError, TypeError:
                child = ''

        resource = self._find_resource(resource_path)

        if method == 'DELETE':
            if isinstance(resource, dict):
                del resource[child]
            else:
                for i, elt in enumerate(resource):
                    if self._matches(elt, child):
                        del resource[i]
                        break
        else:
            new_obj = {'id': binascii.b2a_hex(os.urandom(8)), 'name': child, 'created_at': "2012-10-11T20:23:44Z"}

            resource.append(new_obj)

            if resource_path[-1] == 'addons':
                app = self._find_resource(resource_path[0:-1])
                if child in self._addon_callable:
                    self._addon_callable[child](app, child)

        self.save_mock_data()

        return MockResponse({"name":child})

    def lookup_obj(self, type_name):
        if type_name == 'addons':
            return Addon
        elif type_name == 'apps':
            return App
        else:
            raise TypeError("Unknown path type '%s'" % type_name)

class MockResponse(object):
    def __init__(self, params):
        self._content = json.dumps(params)

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        pass

    @property
    def ok(self):
        return True







