# Max Gadeberg
# Aug 29, 2024

import csv
import requests

ZABBIX_API_URL = 'https://zabbix.example.net/api_jsonrpc.php'
AUTH_TOKEN = ''
CSV_INPUT_FILE = 'host-import.csv'
CSV_OUTPUT_FILE = 'missing-hosts.csv'

headers = {
    'Content-Type': 'application/json-rpc'
}

def zabbix_api_request(data):
    response = requests.post(ZABBIX_API_URL, headers=headers, json=data, timeout=1800)
    response.raise_for_status()
    return response.json()

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
        "auth": AUTH_TOKEN,
        "id": 1
    }
    result = zabbix_api_request(payload)
    if result and 'result' in result:
        return len(result['result']) > 0
    return False

def main():
    missing_hosts = []
    
    with open(CSV_INPUT_FILE, mode='r') as csv_file:
        print('Input file opened')
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            host_name = row['hosts_host'].strip()
            
            if not check_host_exists(host_name):
                print(host_name)
                missing_hosts.append({
                    'hosts_host': host_name,
                    'hosts_proxy_name': row['hosts_proxy_name'].strip(),
                    'hosts_templates_name': row['hosts_templates_name'].strip(),
                    'hosts_group_name': row['hosts_group_name'].strip(),
                    'hosts_interfaces_useip': row['hosts_interfaces_useip'].strip(),
                    'hosts_interfaces_ip': row['hosts_interfaces_ip'].strip(),
                    'hosts_interfaces_dns': row['hosts_interfaces_dns'].strip(),
                    'hosts_interface_details_community': row['hosts_interface_details_community'].strip(),
                    'hosts_interface_details_version': row['hosts_interface_details_version'].strip(),
                    'hosts_tag_name': row['hosts_tag_name'].strip(),
                    'hosts_tag_value': row['hosts_tag_value'].strip(),
                    'import': row['import'].strip()
                })

    with open(CSV_OUTPUT_FILE, mode='w', newline='') as csv_file:
        print('Output file opened')
        fieldnames = [
            'hosts_host',
            'hosts_proxy_name',
            'hosts_templates_name',
            'hosts_group_name',
            'hosts_interfaces_useip',
            'hosts_interfaces_ip',
            'hosts_interfaces_dns',
            'hosts_interface_details_community',
            'hosts_interface_details_version',
            'hosts_tag_name',
            'hosts_tag_value',
            'import'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(missing_hosts)

    print(f"Missing hosts have been written to {CSV_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
