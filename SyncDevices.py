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
snipeit_new_asset_label = config.get('SnipeIT', 'snipeit_new_asset_label')

#UNMS Authentication
data = """{ \"password\": \"""" + unms_api_password + """\", \"username\": \"""" + unms_api_user + """\", \"sessionTimeout\": 3600000}"""
returned_header = requests.post(unms_url + '/v2.1/user/login', data=data, json=True)
unms_headers = {'x-auth-token': returned_header.headers['x-auth-token']}

#SnipeIT Authentication
snipeit_headers = {"Authorization": "Bearer " + snipeit_api_key, "Accept": "application/json"}

#Get List of Devices from UNMS
unms_devices_raw = requests.get(unms_url + '/v2.1/devices', headers=unms_headers).json()

#Get List of Devices from SnipeIT
snipeit_assets = requests.get(snipeit_url + '/api/v1/hardware', headers=snipeit_headers).json()['rows']
snipeit_serial_numbers = []
for asset in snipeit_assets:
    snipeit_serial_numbers.append(asset['serial'])

print(snipeit_serial_numbers)
#Remove Existing Device
new_unms_devices = []
new_unms_devices[:] = [d for d in unms_devices_raw if d['identification']['mac'] not in snipeit_serial_numbers]

#Get List of Models from SnipeIT
snipeit_models = requests.get(snipeit_url + '/api/v1/models', headers=snipeit_headers).json()['rows']
snipeit_model_numbers = []
for model in snipeit_models:
    snipeit_model_numbers.append(model['model_number'])

#Make List of New UNMS Models
unms_models = new_unms_devices
new_unms_models = []
new_unms_models[:] = [d for d in unms_models if d['identification']['model'] not in snipeit_model_numbers]

print(new_unms_models)

#Prep New Models List for Post
new_models_with_duplicates = []
for model in new_unms_models:
    new_model = {}
    new_model['name'] = model['identification']['modelName']
    new_model['model_number'] = model['identification']['model']
    new_model['category_id'] = '13'
    new_model['manufacturer_id'] = '1'
    new_models_with_duplicates.append(new_model)

#Remove Duplicates from New Models Post List)) for item in
new_models = [dict(tupled) for tupled in set(tuple(model.items()) for model in new_models_with_duplicates)]

#Post New Models to SnipeIT
for model in new_models:
    response = requests.post(snipeit_url + '/api/v1/models', data=model, headers=snipeit_headers)
    print('Model "' + model['name'] + '" Adding')
    print(response)

#Get List of Existing Assets Tags & Determine Next Available Asset Tag
highest_asset_tag = 0
for asset in snipeit_assets:
    if int(asset['asset_tag']) >= highest_asset_tag:
        highest_asset_tag = int(asset['asset_tag'])
next_asset_tag = highest_asset_tag + 1
print("Next Available Asset Tag is " + str(next_asset_tag))

#Get Status Labels from SnipeIT and Collect Label for New Assets
snipeit_raw_labels = requests.get(snipeit_url + '/api/v1/statuslabels', headers=snipeit_headers).json()
snipeit_labels = snipeit_raw_labels['rows']
new_asset_label = {}
for label in snipeit_labels:
   if label['name'] == snipeit_new_asset_label:
       new_asset_label = label

#Get Updated Models List from SnipeIT
snipeit_updated_models = requests.get(snipeit_url + '/api/v1/models', headers=snipeit_headers).json()['rows']

print(snipeit_updated_models)
#Add Model ID to New Devices
for device in new_unms_devices:
    for model in snipeit_updated_models:
        if device['identification']['modelName'] == model['name']:
            device['model_id'] = model['id']
            print(device)
            break
        else:
            continue

#Build New Asset List
new_assets = []
for device in new_unms_devices:
    new_asset = {}
    new_asset['asset_tag'] = next_asset_tag
    new_asset['name'] = device['identification']['modelName']
    new_asset['serial'] = device['identification']['mac']
    new_asset['model_id'] = device['model_id']
    new_asset['model_number'] = device['identification']['model']
    new_asset['status_id'] = new_asset_label['id']
    new_asset['manufacturer'] = {'name': "Ubiquiti"}
    new_assets.append(new_asset)
    next_asset_tag += 1



#Post New Assets to SnipeIT
for asset in new_assets:
    response = requests.post(snipeit_url + '/api/v1/hardware', data=asset, headers=snipeit_headers)
    print('Asset "' + asset['name'] + ': ' + asset['serial'] + '" Adding')
    print(response)