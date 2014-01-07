import yaml
import pdb
import binascii
import os

from .api import Heroku
from .structures import KeyedListResource
from .models import Addon


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

    def __init__(self, version=None):
        self._addon_callable = {}
        return super(HerokuMock, self).__init__(version=version)

    def set_addon_configure(self, addon_name, callable):
        self._addon_callable[addon_name] = callable

    def _find_resource(self, resource):
        top = HerokuMock.data
        for elt in resource:
            if elt in top:
                top = top[elt]
            elif isinstance(top, (list, tuple)):
                for child in top:
                    if ('id' in child and child['id'] == elt) or ('name' in child and child['name'] == elt):
                        top = child
                        break 
            else:
                raise ValueError("bad resource index %s" % elt)
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
        print "_get_resources (self: %s), resource: %s, obj: %s" % (str(self), str(resource), str(obj))

        data = HerokuMock.data

        if type(resource) is tuple:
            data = self._find_resource(list(resource)[0:-1])
            resource = list(resource)[-1]

        if resource in data:
            source = data[resource]
        else:
            return []

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
        child = resource_path.pop()

        resource = self._find_resource(resource_path)
        new_obj = {'id': binascii.b2a_hex(os.urandom(8)), 'name': child}
        resource.append(new_obj)
        if resource_path[-1] == 'addons':
            app = self._find_resource(resource_path[0:-1])
            if child in self._addon_callable:
                self._addon_callable[child](app, child)

        return MockResponse()

class MockResponse(object):
    def raise_for_status(self):
        pass








