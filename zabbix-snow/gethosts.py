# Max Gadeberg
# Aug 29, 2024

import csv
import logging
import requests

zabbix_url = 'https://zabbix.example.net/api_jsonrpc.php'
zabbix_auth_token = ''  # Make sure to fill this in

def get_zabbix_hosts():
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid", "name", "host", "status"],
                "selectInterfaces": ["ip", "dns", "main", "type", "useip"],
                "selectTags": "extend",
                "selectInventory": ["tag", "value"],
            },
            "auth": zabbix_auth_token,
            "id": 1
        }
        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        hosts = data.get('result', [])
        print(f"Retrieved {len(hosts)} hosts.")
        return hosts
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching Zabbix hosts: {e}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error in get_zabbix_hosts: {e}')
        return []

def get_items_for_hosts(item_keys):
    try:
        print('|'.join(item_keys))
        print(item_keys)
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["hostid", "itemid", "lastvalue", "key_"],
                "selectHosts": True,
                "searchWildcardsEnabled": True,
                "search": {
                    "key_": item_keys
                },
                "searchByAny": "true",
                "sortfield": "itemid",
                "sortorder": "DESC"
            },
            "auth": zabbix_auth_token,
            "id": 1
        }
        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        items = data.get('result', [])
        print(f"Retrieved {len(items)} items.")
        return items
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching Zabbix item data: {e}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error in get_items_for_hosts: {e}')
        return []

def load_item_keys(filename='items.csv'):
    item_keys = []
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item_key = row.get('Item Key', '').strip()
                if item_key and row['Enabled'].lower() == 'true':
                    item_keys.append(item_key)
        print(f"Loaded item keys: {item_keys}")
        return item_keys
    except Exception as e:
        logging.error(f'Error reading item keys from {filename}: {e}')
        return []

def save_hosts_to_csv(hosts, items, item_keys, filename='zabbix_hosts.csv'):
    # Create a dictionary for quick lookup of item data by hostid and key
    items_by_hostid = {}
    for item in items:
        host_id = item['hostid']
        key = item['key_']
        if host_id not in items_by_hostid:
            items_by_hostid[host_id] = {}
        items_by_hostid[host_id][key] = item['lastvalue']

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row with dynamic item keys as columns
        header = ["IP", "Host Name", "DNS", "Enabled/Disabled", "SNMP Availability"] + item_keys
        writer.writerow(header)
        
        for host in hosts:
            ip = dns = snmp_availability = None
            for interface in host.get('interfaces', []):
                if interface['main'] == '1':
                    ip = interface['ip'] if interface['useip'] == '1' else None
                    dns = interface['dns'] if interface['useip'] == '0' else None
                    # Type '2' generally indicates SNMP interface in Zabbix
                    snmp_availability = 'Available' if interface['type'] == '2' else 'Not Available'
                    break
            
            host_name = host.get('host', '')
            status = 'Enabled' if host.get('status') == '0' else 'Disabled'
            
            # Retrieve the last values for each item key
            row = [ip, host_name, dns, status, snmp_availability]
            for key in item_keys:
                row.append(items_by_hostid.get(host['hostid'], {}).get(key, 'N/A'))
            
            print(f"Writing row: {row}")
            writer.writerow(row)

if __name__ == "__main__":
    item_keys = load_item_keys('items.csv')  # Load item keys from items.csv
    hosts = get_zabbix_hosts()
    if hosts and item_keys:
        items = get_items_for_hosts(item_keys)
        if items:
            save_hosts_to_csv(hosts, items, item_keys)
