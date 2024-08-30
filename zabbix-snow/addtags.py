# Max Gadeberg
# Aug 29, 2024

import requests
import json

zabbix_url = 'https://zabbix.example.net/api_jsonrpc.php'
#zabbix_auth_token = '' #dev
zabbix_auth_token = '' #prod

servicenow_url = 'https://example.service-now.com/api/now/table/cmdb_ci_netgear'
servicenow_user = ''
servicenow_password = ''

def fetch_all_hosts(zabbix_url, auth_token):
    all_hosts = []
    offset = 0
    limit = 10000 


    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "selectInterfaces": "extend",
            "selectTags": "extend",
            "selectHostGroups": "extend"
        },
        "auth": auth_token,
        "id": 1
    }

    try:
        response = requests.post(zabbix_url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        hosts = data.get('result', [])

        all_hosts.extend(hosts)

    except requests.exceptions.RequestException as e:
        print(f"Request to Zabbix failed: {e}")
        return []  # Return an empty list on failure

    except json.decoder.JSONDecodeError as e:
        print(f"Failed to parse JSON response from Zabbix: {e}")
        print(f"Raw response content: {response.text}")  # Print raw content for debugging
        return []  # Return an empty list on failure

    return all_hosts


hosts_info = fetch_all_hosts(zabbix_url, zabbix_auth_token)

servicenow_params = {
            'operational_status': '1',
            'sysparm_fields': 'u_cpe_dns,u_mgmt_ip_address,u_sid,u_customer,operational_status',
            'device_type': 'cpe',
        }
servicenow_response = requests.get(servicenow_url, params=servicenow_params, auth=(servicenow_user, servicenow_password))
servicenow_data = servicenow_response.json()
servicenow_result = servicenow_data.get('result', [])

def filter_by_ip(data, search_ip):
    return [record for record in data if search_ip in record.get('u_mgmt_ip_address', '')]

for host in hosts_info:
    print(host)
    host_id = host.get('hostid')
    ip = None
    groupids = []

    if host.get('interfaces'):
        ip = host['interfaces'][0].get('ip')

    if host.get('hostgroups'):
        groupids = [group.get('groupid') for group in host['hostgroups']]
        #print(groupids)

    tags = host.get('tags', [])
    tag_dict = {tag['tag']: tag['value'] for tag in tags}

    if ip and ip != '127.0.0.1':
        if "209" in groupids:
            if servicenow_result:
                servicenow_filtered_results = filter_by_ip(servicenow_result, ip)
                
                if servicenow_filtered_results:
                    u_sid = servicenow_filtered_results[0].get('u_sid')
                    print(tag_dict)

                    if 'CID' in tag_dict:
                        if tag_dict['CID'] == u_sid:
                            print('CID already exists, skipping')
                        else:
                            print('CID already exists, but different than found one')
                            print('Existing CID:', tag_dict['CID'])
                            print('New CID:', u_sid)
                    else:
                        # Handle case where 'CID' does not exist in tag_dict
                        tag_dict['CID'] = u_sid
                        print('CID does not exist in tag_dict')

                        zabbix_update_payload = {
                            "jsonrpc": "2.0",
                            "method": "host.update",
                            "params": {
                                "hostid": host_id,
                                "tags": [{"tag": tag, "value": value} for tag, value in tag_dict.items()]
                            },
                            "auth": zabbix_auth_token,
                            "id": 1
                        }

                        # Uncomment to perform the API call
                        update_response = requests.post(zabbix_url, json=zabbix_update_payload)
                        update_data = update_response.json()
                        print(f'Updated host {host_id} new tags: {[{"tag": tag, "value": value} for tag, value in tag_dict.items()]}')

                else:
                    print('Couldnt find IP')
            #else:
                #print(f'No u_sid found for IP {ip}')
        #else:
            #print(f'No matching records found in ServiceNow for IP {ip}')
    #else:
        #if ip != '127.0.0.1':
            #print(f'No IP found for host {host_id}')
