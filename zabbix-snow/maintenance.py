# Max Gadeberg
# Aug 29, 2024

import requests
import logging
from collections import defaultdict
from datetime import datetime

servicenow_url = "https://example.service-now.com/api/now/table/u_change_service?sysparm_query=chg_start_date%3Ejavascript%3Ags.endOfToday()&sysparm_fields=chg_number%2Cbs_name%2Cbs_u_cpe_dns%2Cchg_start_date%2Cchg_end_date&sysparm_limit=1000"
zabbix_url = 'https://zabbix.example.net/api_jsonrpc.php'
zabbix_auth_token = ''



def get_servicenow_change_orders():
    
    try:
        payload = {}
        headers = {
            'Authorization': '',
            'Cookie': ''
        }
        response = requests.request("GET", servicenow_url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        mydata = data.get('result',[])
        change_orders = defaultdict(list)
        
        for orders in mydata:
            chg_number = orders.get('chg_number')
            circuit = orders.get('bs_name')
            start_time = orders.get('chg_start_date')
            end_time = orders.get('chg_end_date')
            
            change_orders[chg_number, start_time, end_time].append(circuit)
            
        return change_orders
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching ServiceNow change orders: {e}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error in get_servicenow_change_orders: {e}')
        return []




def get_zabbix_hosts():
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "selectTags": "extend",
            },
            "auth": zabbix_auth_token,
            "id": 1
        }
        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        hosts = data.get('result', [])
        return hosts
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching Zabbix hosts: {e}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error in get_zabbix_hosts: {e}')
        return []




def find_matching_hosts(circuits, hosts):
    matching_hosts = []
    for host in hosts:
        for tag in host.get('tags', []):
            tag_value = tag.get('value')
            if tag_value in circuits:
                matching_hosts.append({
                    'hostid': host.get('hostid'),
                    'tag': tag.get('tag'),
                    'value': tag_value
                })
                logging.info(f'Found matching host for circuit {tag_value}')
    return matching_hosts




def get_maintenance_in_zabbix(chg_number):
    try:
        headers = {
            'Content-Type': 'application/json-rpc'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "maintenance.get",
            "params": {
                "filter": {
                    "name": chg_number
                },
                "output": "extend"
            },
            "auth": zabbix_auth_token,
            "id": 1
        }
        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # print(data)
        maintenances = data.get('result', [])
        # print(f"Maintenaces: {maintenances}")
        return maintenances
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching maintenance from Zabbix: {e}')
        return []
    except Exception as e:
        logging.error(f'Unexpected error in get_maintenance_in_zabbix: {e}')
        return []




def create_maintenance_in_zabbix(chg_order, start_time, end_time, hostid):
    try:
        hosts_formatted = [{'hostid': int(hostid)} for hostid in hostid]
        print(f"Hosts formatted: {hosts_formatted}")

        print(start_time)

        dt_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        print(dt_start_time)

        # Convert to Unix time
        start_unix = int(dt_start_time.timestamp())
        end_unix = int(dt_end_time.timestamp())

        print(type(start_unix))

        headers = {
            'Content-Type': 'application/json-rpc'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "maintenance.create",
            "params": {
                "name": f"{chg_order}",
                "active_since": start_unix,
                "active_till": end_unix,
                "tags_evaltype": 0,
                "hosts": hosts_formatted,
                "tags": [
                    {
                        "tag": "change order",
                        "value": chg_order
                    }
                ],
                "timeperiods": [
                    {
                        "timeperiod_type": 0
                    }
                ]
            },
            "auth": zabbix_auth_token,
            "id": 1
        }

        print(payload)

        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
        maintenance_id = data.get('result', {}).get('maintenanceids', [])[0]
        return maintenance_id
    except requests.exceptions.RequestException as e:
        logging.error(f'Error creating maintenance in Zabbix: {e}')
        return None
    except Exception as e:
        logging.error(f'Unexpected error in create_maintenance_in_zabbix: {e}')
        return None




def update_maintenance_in_zabbix(maintenance_id, start_time, end_time, hostid):
    try:
        
        hosts_formatted = [{'hostid': int(hostid)} for hostid in hostid]

        dt_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        print(dt_start_time)

        # Convert to Unix time
        start_unix = int(dt_start_time.timestamp())
        end_unix = int(dt_end_time.timestamp())

        headers = {
            'Content-Type': 'application/json-rpc'
        }
        payload = {
            "jsonrpc": "2.0",
            "method": "maintenance.update", 
            "params": {
                "hosts": hosts_formatted,
                "maintenanceid": maintenance_id,
                "active_since": start_unix,
                "active_till": end_unix
            },
            "auth": zabbix_auth_token,
            "id": 1
        }
        response = requests.post(zabbix_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f'Data: {data}')
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f'Error updating maintenance in Zabbix: {e}')
        return False
    except Exception as e:
        logging.error(f'Unexpected error in update_maintenance_in_zabbix: {e}')
        return False




def document_mismatch_in_document_system(circuit_name):
    logging.warning(f'Maintenance for circuit {circuit_name} exists in Zabbix but not in ServiceNow.')



def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='script.log',
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    logging.info('Script started.')

    try:
        change_orders = get_servicenow_change_orders()
        logging.info(f'Fetched {len(change_orders)} change orders from ServiceNow.')

        hosts = get_zabbix_hosts()
        logging.info(f'Fetched {len(hosts)} hosts from Zabbix.')

        for (chg_number, start_time, end_time), circuits in change_orders.items():
            logging.info(f"Processing change order {chg_number} from {start_time} to {end_time}")

            matching_hosts = find_matching_hosts(circuits, hosts)
            logging.info(f"Found {len(matching_hosts)} matching hosts")

            print(matching_hosts)

            for circuit in circuits:
                logging.info(f"Processing circuit: {circuit}")

                if matching_hosts:
                    hostid_list = [item['hostid'] for item in matching_hosts]

                    logging.info(f"Matching hosts IDS: {hostid_list}")
                    zabbix_maintenances = get_maintenance_in_zabbix(chg_number)
                    logging.info(f"Zabbix maintenances: {zabbix_maintenances}")

                    if zabbix_maintenances:
                        maintenance_id = zabbix_maintenances[0]['maintenanceid']
                        update_success = update_maintenance_in_zabbix(maintenance_id, start_time, end_time, hostid_list)
                        # update_success = True
                        if update_success:
                            logging.info(f'Updated maintenance in Zabbix for circuit {circuit}.')
                        else:
                            logging.error(f'Failed to update maintenance in Zabbix for circuit {circuit}.')
                    else:
                        maintenance_id = create_maintenance_in_zabbix(chg_number, start_time, end_time, hostid_list)
                        # maintenance_id = True
                        if maintenance_id:
                            logging.info(f'Created maintenance in Zabbix for circuit {circuit}.')
                        else:
                            logging.error(f'Failed to create maintenance in Zabbix for circuit {circuit}.')
                else:
                    logging.warning(f'No matching hosts found in Zabbix for circuit {circuit}.')
            
    except Exception as e:
        logging.error(f'Unexpected error in main: {e}')

    logging.info('Script completed.')


if __name__ == "__main__":
    main()
