# Max Gadeberg
# Aug 29, 2024

import requests
import json
import logging
import creds
import os

# Configure logging
logging.basicConfig(filename='audit_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

snow_url = "https://dev.service-now.com/api/now/table/x_noann_add_drop_m_add_drop_modify?sysparm_query=opened_atONLast%207%20days%40javascript%3Ags.beginningOfToday()%40javascript%3Ags.endOfToday()^state=3"

# Zabbix API credentials
zabbix_url = 'https://zabbix.example.net/api_jsonrpc.php'

def zabbix_host_get(search_params):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": "extend",
            "selectInterfaces": "extend",
            "search": search_params,
            "searchByAny": True,
        },
        "auth": creds.auth_token,
        "id": 1
    }

    headers = {'content-type': 'application/json'}
    response = requests.post(zabbix_url, data=json.dumps(payload), headers=headers)

    try:
        response_data = response.json()
    except ValueError:
        logging.error("Invalid JSON response received from Zabbix API.")
        return None
    
    if 'error' in response_data:
        logging.error(f"Zabbix API returned an error: {response_data['error']}")
        return None
    
    if 'result' in response_data:
        return response_data['result']
    else:
        logging.error("Zabbix API did not return a 'result' key in the response.")
        return None

def zabbix_host_update(host_id, new_data):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": host_id,
            **new_data
        },
        "auth": creds.auth_token,
        "id": 1
    }
    headers = {'content-type': 'application/json'}
    response = requests.post(zabbix_url, data=json.dumps(payload), headers=headers)
    return response.json()['result']

def zabbix_host_create(host_data):
    if 'dns' in host_data['interfaces'][0]:
        host_data['interfaces'][0]['dns'] = host_data['interfaces'][0]['dns'].strip()

    payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": host_data,
        "auth": creds.auth_token,
        "id": 1
    }
    headers = {'content-type': 'application/json'}
    response = requests.post(zabbix_url, data=json.dumps(payload), headers=headers)
    
    try:
        response_data = response.json()
    except ValueError:
        logging.error("Invalid JSON response received from Zabbix API when creating host.")
        return None
    
    if 'error' in response_data:
        logging.error(f"Zabbix API returned an error when creating host: {response_data['error']}")
        return None
    
    if 'result' in response_data:
        return response_data['result']
    else:
        logging.error("Zabbix API did not return a 'result' key in the response when creating host.")
        return None

def remove_domain_suffix(dns_name):
    suffixes = [".ncs.example.net", ".nmc.example.net", ".kpud.net", ".clallampud.net"]
    
    for suffix in suffixes:
        if dns_name.endswith(suffix):
            return dns_name.replace(suffix, "")
    
    return dns_name

def process_snow_records():
    response = requests.get(snow_url, auth=(creds.snow_username, creds.snow_password))
    logging.info("INFO - Starting new run through ServiceNow records.\n")
    
    if response.status_code == 200:
        data = response.json()

        for record in data.get('result', []):
            add_drop_modify = record.get('add_drop_modify')
            u_adm_ip_addr = record.get('u_adm_ip_addr')
            u_nn_adm_oldfqdn = record.get('u_nn_adm_oldfqdn')
            # u_fqdn = record.get('u_fqdn')
            u_nn_adm_newip = record.get('u_nn_adm_newip')
            # u_nn_adm_newfqdn = record.get('u_nn_adm_newfqdn')
            u_nn_adm_existingip = record.get('u_nn_adm_existingip')
            u_nn_adm_zone = record.get('u_nn_adm_zone')
            u_nn_adm_hostname = record.get('u_nn_adm_hostname')
            u_nn_adm_newhostname = record.get('u_nn_adm_newhostname')

            if u_nn_adm_hostname != '' and u_nn_adm_zone != '':
                fqdn = u_nn_adm_hostname + u_nn_adm_zone
            else:
                logging.error(f'Hostname or domain name missing: u_nn_adm_hostname: {u_nn_adm_hostname} u_nn_adm_zone: {u_nn_adm_zone}')

            if u_nn_adm_newhostname != '' and u_nn_adm_zone != '':
                new_fqdn = u_nn_adm_newhostname + u_nn_adm_zone
            else:
                logging.error(f'New hostname or domain name missing: u_nn_adm_newhostname: {u_nn_adm_newhostname} u_nn_adm_zone: {u_nn_adm_zone}')

            if add_drop_modify == '0':
                action = 'ADD'
            elif add_drop_modify == '2':
                action = 'MODIFY'

            logging.info(f"INFO - Processing record with ADM: {action}, DNS: {fqdn or new_fqdn}, IP: {u_adm_ip_addr or u_nn_adm_newip}")

            if add_drop_modify == '2':
                if fqdn != '' and new_fqdn != '' and u_nn_adm_existingip != '' and u_nn_adm_newip != '':
                    search_params = {}
                    search_params['ip'] = [u_nn_adm_existingip, u_nn_adm_newip]
                    hosts = zabbix_host_get(search_params)

                    nslresponse = os.system('nslookup ' + new_fqdn)

                    if nslresponse == 0:
                        logging.info(f"INFO - {new_fqdn} found")
                    else:
                        logging.error(f"ERROR - {new_fqdn} not found")
                    

                    pingresponse = os.system("ping -c 1 " + u_nn_adm_newip)

                    if pingresponse == 0:
                        logging.info(f"INFO - {u_nn_adm_newip} pingable")
                    else:
                        logging.error(f"ERROR - {u_nn_adm_newip} not pingable")

                    if hosts:
                        host_id = hosts[0]['hostid']
                        current_dns = hosts[0]['interfaces'][0]['dns']
                        current_ip = hosts[0]['interfaces'][0]['ip']

                        if current_dns != new_fqdn.strip() or current_ip != u_nn_adm_newip.strip():
                            new_data = {
                                "ip": u_nn_adm_newip,
                                "dns": new_fqdn.strip()
                            }
                            zabbix_host_update(host_id, new_data)
                            logging.info(f"INFO - Updated host {host_id} with new data: {new_data}")
                        else:
                            logging.info(f"INFO - No update needed for host {host_id}. DNS and IP are already up-to-date.")
                    else:
                        host_data = {
                            "host": u_nn_adm_hostname,
                            "interfaces": [{
                                "type": 2,
                                "main": 1,
                                "useip": 0,
                                "ip": u_nn_adm_newip,
                                "dns": new_fqdn.strip(),
                                "port": "161",
                                "details": {
                                    "version": '2',
                                    "community" : "{$SNMP_COMMUNITY}"
                                },
                            }],
                            "groups": [{"groupid": "257"}],
                            "templates": [{"templateid": "10564"}],
                            "inventory_mode": 1,
                            "monitored_by": 1,
                            "proxyid":  2
                        }
                        zabbix_host_create(host_data)
                        logging.info(f"INFO - Host not found for {u_nn_adm_oldfqdn}, added new host: {host_data}")

                else:
                    logging.warning(f"ERROR - Record {record.get('sys_id')} with ADM=2 has incomplete FQDN data.")

            elif add_drop_modify == '0':
                if fqdn != '' and u_adm_ip_addr != '':
                    search_params = {}
                    search_params['ip'] = u_adm_ip_addr
                    search_params['dns'] = fqdn

                    nslresponse = os.system('nslookup ' + fqdn)

                    if nslresponse == 0:
                        logging.info(f"INFO - {fqdn} found")
                    else:
                        logging.error(f"ERROR - {fqdn} not found")
                    

                    pingresponse = os.system("ping -c 1 " + u_adm_ip_addr)

                    if pingresponse == 0:
                        logging.info(f"INFO - {u_adm_ip_addr} pingable")
                    else:
                        logging.error(f"ERROR - {u_adm_ip_addr} not pingable")
                    
                    hosts = zabbix_host_get(search_params)
                    if hosts:
                        logging.info(f"INFO - Host already exists in Zabbix for IP: {u_adm_ip_addr}, FQDN: {fqdn}")
                    else:
                        host_data = {
                            "host": u_nn_adm_hostname,
                            "interfaces": [{
                                "type": 2,
                                "main": 1,
                                "useip": 0,
                                "ip": u_adm_ip_addr,
                                "dns": fqdn.strip(),
                                "port": "161",
                                "details": {
                                    "version": '2',
                                    "community" : "{$SNMP_COMMUNITY}"
                                },
                            }],
                            "groups": [{"groupid": "257"}],
                            "templates": [{"templateid": "10564"}],
                            "inventory_mode": 1,
                            "monitored_by": 1,
                            "proxyid":  2
                        }
                        zabbix_host_create(host_data)
                        logging.info(f"INFO - Added new host with data: {host_data}")
                else:
                    logging.warning(f"ERROR - Record {record.get('sys_id')} with ADM=0 has incomplete IP or FQDN data.")

            logging.info("\n")  # Space out each record in the log

    else:
        logging.error(f"ERROR - Failed to retrieve data from ServiceNow: {response.status_code}, {response.text}")

    logging.info("INFO - Finished processing ServiceNow records.\n")

# Execute the processing function
process_snow_records()
