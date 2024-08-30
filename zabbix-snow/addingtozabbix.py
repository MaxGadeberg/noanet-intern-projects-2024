# Max Gadeberg
# Aug 29, 2024

import csv
import requests 
ZABBIX_API_URL = 'https://zabbix.example.net/api_jsonrpc.php' # 

headers = {
    'Content-Type': 'application/json-rpc'
}

auth_token = '' # 

# -------------------------------------------


def zabbix_api_request(data):
    response = requests.post(ZABBIX_API_URL, headers=headers, json=data, timeout=1800)
    response.raise_for_status()
    return response.json()


# -------------------------------------------

def get_groupid(hosts_group_name):
    if hosts_group_name != '' or hosts_group_name != 'undefined':
        payload = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend",
                "filter": {
                    "name": [
                        hosts_group_name
                    ]
                }
            },
            "auth": auth_token,
            "id": 1
        }
        result = zabbix_api_request(payload)
        if result and 'result' in result:
            if len(result['result']) > 0:
                return result['result'][0]['groupid']  # Return existing group ID
            else:
                # Group not found, create a new group
                return create_host_group(hosts_group_name)
        else:
            raise Exception(f"Failed to get group information for {hosts_group_name}")
    else:
        raise Exception(f"Group name undefined or none")

# -------------------------------------------


def create_host_group(hosts_group_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.create",
        "params": {
            "name": hosts_group_name
        },
        "auth": auth_token,
        "id": 1
    }
    result = zabbix_api_request(payload)
    print(result)
    if result and 'result' in result:
        return result['result']['groupids'][0]  # Return the newly created group ID
    else:
        raise Exception(f"Failed to create group {hosts_group_name}")


# -------------------------------------------


def main():
    with open('missing-hosts.csv', mode='r') as csv_file:
        print('file opened')
        csv_reader = csv.DictReader(csv_file)

        for _ in range(201):
            next(csv_reader)

        for row in csv_reader:
            if row['import'].strip() == '0':
                print(f"Skipping import for host {row['hosts_host'].strip()} as per CSV directive.")
                continue
            
            # Retrieve the group ID
            groupid = get_groupid(row['hosts_group_name'].strip())
            if not groupid:
                print(f"Failed to find groupid for {row['hosts_group_name'].strip()}")
                continue

            host_exists = check_host_exists(row['hosts_host'].strip())
            if host_exists:
                print(f"Host {row['hosts_host'].strip()} already exists, skipping creation.")
                continue
                
            tags = []
            if row['hosts_tag_name'].strip() and row['hosts_tag_value'].strip():
                tags.append({
                    "tag": row['hosts_tag_name'].strip(),
                    "value": row['hosts_tag_value'].strip()
                })

            payload = {
                "jsonrpc": "2.0",
                "method": "host.create",
                "params": {
                    "host": row['hosts_host'].strip(),
                    "status": 1,
                    "interfaces": [
                        {
                            "type": 2,
                            "main": 1,
                            "useip": int(row['hosts_interfaces_useip']),
                            "ip": row['hosts_interfaces_ip'].strip(),
                            "dns": row['hosts_interfaces_dns'].strip(),
                            "port": "161",
                            "details": {
                                "version": int(row['hosts_interface_details_version']),
                                "community": "{$SNMP_COMMUNITY}" if row['hosts_interface_details_community'].strip() == "N0An3T" else row['hosts_interface_details_community'].strip()
                            }
                        }
                    ],
                    "groups": [
                        {
                            "groupid": groupid
                        }
                    ],
                    "templates": [
                        {
                            "templateid": "10564"
                        }
                    ],
                    "tags": tags,
                    "inventory_mode": 1,
                    "monitored_by": 1,
                    "proxyid": 2 if row['hosts_proxy_name'].strip() == "olympia-proxy" else 1
                },
                "auth": auth_token,
                "id": 1
            }

            # Send the request to create the host
            result = zabbix_api_request(payload)
            print(f"Host {row['hosts_host'].strip()} created successfully")




# -------------------------------------------


def check_host_exists(host_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host"],
            "filter": {
                "host": [host_name]
            }
        },
        "auth": auth_token,
        "id": 1
    }
    result = zabbix_api_request(payload)
    if result and 'result' in result:
        return len(result['result']) > 0
    return False


# -------------------------------------------


if __name__ == "__main__":
    main()
