import requests
import configparser
import re

# Parse Config File
config = configparser.ConfigParser()
config.readfp(open(r'config.ini'))
unms_url = config.get('UNMS', 'unms_url')
unms_api_user = config.get('UNMS', 'unms_api_user')
unms_api_password = config.get('UNMS', 'unms_api_password')
snipeit_url = config.get('SnipeIT', 'snipeit_url')
snipeit_api_key = config.get('SnipeIT', 'snipeit_api_key')
snipeit_new_asset_label = config.get('SnipeIT', 'snipeit_new_asset_label')
snipeit_query_limit = config.get('SnipeIT', 'snipeit_query_limit')
snipeit_checkedIn = config.get('SnipeIT', 'snipeit_checkedIn')
snipeit_checkedOut = config.get('SnipeIT', 'snipeit_checkedOut')

# UNMS Authentication
data = """{ \"password\": \"""" + unms_api_password + """\", \"username\": \"""" + unms_api_user + """\", \"sessionTimeout\": 3600000}"""
returned_header = requests.post(unms_url + '/v2.1/user/login', data=data, json=True)
unms_headers = {'x-auth-token': returned_header.headers['x-auth-token']}

# SnipeIT Authentication
snipeit_headers = {"Authorization": "Bearer " + snipeit_api_key, "Accept": "application/json"}

# Get List of Devices from UNMS
print("gathering devices from UNMS...")
unms_devices = requests.get(unms_url + '/v2.1/devices', headers=unms_headers).json()

# Get List of Devices from SnipeIT
print("gathering assets from Snipe-IT...")
snipeit_assets = requests.get(snipeit_url + '/api/v1/hardware', headers=snipeit_headers, params={'limit': snipeit_query_limit}).json()['rows']

# Get List of Sites from SnipeIT
print('gathering sites from SnipeIT...')
snipeit_locations = requests.get(snipeit_url + '/api/v1/locations', headers=snipeit_headers, params={'limit': snipeit_query_limit}).json()['rows']

# Seperate SnipeIT Devices into Checked-In Out
snipeit_checked_in = [d for d in snipeit_assets if d['status_label']['name'] == snipeit_checkedIn]
snipeit_checked_out = [d for d in snipeit_assets if d['status_label']['name'] == snipeit_checkedOut]

# Seperate Assets into Checked-In Out
asset_checked_in = []
for device in unms_devices:
    for asset in snipeit_checked_in:
        if device['identification']['mac'] == asset['serial']:
            asset_checked_in.append(asset)
            break
        else:
            continue

asset_checked_out = []
for device in unms_devices:
    for asset in snipeit_checked_out:
        if device['identification']['mac'] == asset['serial']:
            asset_checked_out.append(device)
            break
        else:
            continue

# List Checked-Out w/ Site Changes
print('checking for site changes...')
to_post = []
for asset in asset_checked_out:
    for device in unms_devices:
        if asset['serial'] == device['identification']['mac']:
            if asset['location'] != device['identification']['site']:
                asset['new_location'] = device['identification']['site']['name']
                to_post.append(asset)

# List Checked-In w/ New Site
print('getting new assets...')
for asset in asset_checked_in:
    for device in unms_devices:
        if asset['serial'] == device['identification']['mac']:
            asset['location'] = device['identification']['site']['name']
            to_post.append(asset)
            break
        else:
            continue

# Prep Changes for Post
print('preparing changes for commit...')
post_items = []
for asset in to_post:
    item = {}
    item['id'] = asset['id']
    item['checkout_to_type'] = 'location'
    item['assigned_location'] = asset['location']
    item['note'] = 'checkout from API'
    post_items.append(item)

# Convert Site Name to ID
for item in post_items:
    for location in snipeit_locations:
        if item['assigned_location'] == location['name']:
            item['assigned_location'] = location['id']
            break
        else:
            continue

# Check for Unknown Sites
final_post = []
for item in post_items:
    if re.search('[a-zA-Z]', str(item['assigned_location'])):
        print(str(item['id']), ' site unknown')
    else:
        final_post.append(item)

# Post Changes
print('committing changes...')
for item in final_post:
    response = requests.post(snipeit_url + '/api/v1/hardware/' + str(item['id']) + '/checkout', data=item, headers=snipeit_headers)
    print('checking out ', item['id'])
print("done")