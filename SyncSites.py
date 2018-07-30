import requests
import configparser

#Parse Config File
config = configparser.ConfigParser()
config.readfp(open(r'config.ini'))
unms_url = config.get('UNMS', 'unms_url')
unms_api_user = config.get('UNMS', 'unms_api_user')
unms_api_password = config.get('UNMS', 'unms_api_password')
snipeit_url = config.get('SnipeIT', 'snipeit_url')
snipeit_api_key = config.get('SnipeIT', 'snipeit_api_key')

#UNMS Authentication
data = """{ \"password\": \"""" + unms_api_password + """\", \"username\": \"""" + unms_api_user + """\", \"sessionTimeout\": 3600000}"""
returned_header = requests.post(unms_url + '/v2.1/user/login', data=data, json=True)
unms_headers = {'x-auth-token': returned_header.headers['x-auth-token']}

#SnipeIT Authentication
snipeit_headers = {"Authorization": "Bearer " + snipeit_api_key, "Accept": "application/json"}

#Get Sites from UNMS
unms_sites = requests.get(unms_url + '/v2.1/sites', headers=unms_headers).json()

#Get Sites from SnipeIT
snipeit_locations_raw = requests.get(snipeit_url + '/api/v1/locations', headers=snipeit_headers).json()
snipeit_locations =snipeit_locations_raw['rows']

sjenkins@Stephen-DT:~/Projects/GitHub/UNMS-SnipeIT-Sync$

#Remove Existing Sites
for site in unms_sites:
    for location in snipeit_locations:
        if site['identification']['name'] == location['name']:
            print('Site "' + site['identification']['name'] + '" already exists')
            unms_sites.remove(site)
            break
        else:
            continue

#Add New Sites to SnipeIT
for site in unms_sites:
    add_site = {}
    add_site['name'] = site['identification']['name']
    response = requests.post(snipeit_url + '/api/v1/locations', data=add_site, headers=snipeit_headers)
    print(response)
    print('Site "' + site['identification']['name'] + '" Added')