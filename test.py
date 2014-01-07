import pdb
from heroku.mock import HerokuMock

h = HerokuMock(version=3)
print h.apps
for a in h.apps:
	print a.name + " -- " + a.id

addons = h.apps[0].addons
print addons

def configure_hc_addon(app_dict, addon_name):
	if 'config_vars' not in app_dict:
		app_dict['config_vars'] = {}
	app_dict['config_vars']['HEROKUCONNECT_TENANT_KEY'] = 'abc'

def configure_pg_addon(app_dict, addon_name):
	if 'config_vars' not in app_dict:
		app_dict['config_vars'] = {}
	app_dict['config_vars']['DATABASE_URL'] = 'postgres://localhost'

h.set_addon_configure("herokuconnect", configure_hc_addon)
h.set_addon_configure("heroku-postgresql:dev", configure_pg_addon)

theapp = h.apps[0]
con = theapp.addons.add("herokuconnect")
con = theapp.addons.add("heroku-postgresql:dev")

print theapp.config