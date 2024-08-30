# Max Gadeberg
# Aug 29, 2024

import requests
import logging
from collections import defaultdict
from datetime import datetime

servicenow_url = "https://example.service-now.com/api/now/table/u_change_service?sysparm_query=chg_start_date%3Ejavascript%3Ags.endOfToday()&sysparm_fields=chg_number%2Cbs_name%2Cbs_u_cpe_dns%2Cchg_start_date%2Cchg_end_date&sysparm_limit=1000"
zabbix_url = 'https://zabbix.example.net/api_jsonrpc.php'
zabbix_auth_token = ''


def create_maintenance_in_zabbix(chg_order, start_time, end_time, hostid):
    try:
        hosts_formatted = [{'hostid': int(hostid)} for hostid in hostid]
        print(f"Hosts formatted: {hosts_formatted}")
        formatted_start_time = datetime.timestamp(start_time)
        formatted_end_time = datetime.timestamp(end_time)

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
                "name": f"Maintenance for {chg_order}",
                "active_since": start_unix,
                "active_till": end_unix,
                "tags_evaltype": 0,
                "hosts": hosts_formatted,
                "tags": [
                    {
                        "tag": "change order",
                        "value": chg_order
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
        maintenance_id = data.get('result', {}).get('maintenanceids', [])[0]
        return maintenance_id
    except requests.exceptions.RequestException as e:
        logging.error(f'Error creating maintenance in Zabbix: {e}')
        return None
    except Exception as e:
        logging.error(f'Unexpected error in create_maintenance_in_zabbix: {e}')
        return None
    

mytest = create_maintenance_in_zabbix("CHG0025062", "2024-08-08 07:00:00", "2024-08-08 12:00:00", "['13474']")

print(mytest)