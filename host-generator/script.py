# Max Gadeberg
# Aug 29, 2024

import pandas as pd
import requests
from jinja2 import Environment, FileSystemLoader
import argparse
import json
import logging
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
# Create "config.ini" see example in "config.ini.example"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up command-line argument parsing
parser = argparse.ArgumentParser(description="Process CSV to generate Zabbix API requests.")
parser.add_argument('--csv', required=True, help='Path to the CSV file to be processed.')
parser.add_argument('--test', action='store_true', help='Print JSON payloads without making API requests.')
args = parser.parse_args()

def load_csv(file_path):
    """Load the CSV file into a DataFrame, with error handling for file issues."""
    try:
        return pd.read_csv(file_path, on_bad_lines='skip')
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"No data found in the file: {file_path}")
        raise
    except pd.errors.ParserError:
        logger.error(f"Error parsing the file: {file_path}")
        raise

# Load CSV file
csv_file = args.csv
df = load_csv(csv_file)

# Set up Jinja2 environment
file_loader = FileSystemLoader('./templates')
env = Environment(loader=file_loader)

# Zabbix API details
zabbix_url = config.get('zabbix', 'url')
auth_token = config.get('zabbix', 'auth_token')

def parse_json_field(field_value):
    """Safely parse JSON fields and handle malformed data."""
    if not isinstance(field_value, str):
        logger.warning("Expected string for JSON parsing, but got: %s", type(field_value).__name__)
        return {}
    try:
        field_value = field_value.replace("'", "\"")
        return json.loads(field_value)
    except json.JSONDecodeError as e:
        logger.error("JSONDecodeError: %s for field: %s", e, field_value)
        return {}

def process_row(row, test_mode=False):
    """Process each row to generate JSON payloads and make API requests."""
    logger.info("Processing row with host_name: %s", row.get('host_name', 'Unknown'))

    action = row.get('action')
    if not action:
        logger.warning("No action specified for row with host_name: %s", row.get('host_name', 'Unknown'))
        return

    # Initialize data dictionary
    data = {
        "auth_token": auth_token
    }

    template_file = None
    
    if action == 'c':
        host_type = row.get('host_type', 'default')
        if host_type == 'snmp':
            template_file = 'zabbix_template_snmp.jinja2'
            data.update({
                "host_name": row.get('host_name', ''),
                "ip_address": row.get('ip_address', ''),
                "group_id": int(float(row.get('group_id', '0'))),
                "template_id": int(float(row.get('template_id', '0'))),
                "snmp_community": row.get('snmp_community', ''),
                "version": int(float(row.get('version', 3))) if pd.notna(row.get('version')) else 3,
                "bulk": int(float(row.get('bulk', 0))) if pd.notna(row.get('bulk')) else 0,
                "securityname": row.get('securityname', ''),
                "contextname": row.get('contextname', ''),
                "securitylevel": int(float(row.get('securitylevel', 1))) if pd.notna(row.get('securitylevel')) else 1
            })
        elif host_type == 'encrypted':
            template_file = 'zabbix_template_encrypted.jinja2'
            data.update({
                "host_name": row.get('host_name', ''),
                "ip_address": row.get('ip_address', ''),
                "group_id": int(float(row.get('group_id', '0'))),
                "template_id": int(float(row.get('template_id', '0'))),
                "encrypted_value": row.get('encrypted_value', ''),
                "macros": parse_json_field(row.get('macros', '[]'))
            })
        else:
            template_file = 'zabbix_template_unencrypted.jinja2'
            data.update({
                "host_name": row.get('host_name', ''),
                "ip_address": row.get('ip_address', ''),
                "group_id": int(float(row.get('group_id', '0'))),
                "template_id": int(float(row.get('template_id', '0'))),
                "tags": parse_json_field(row.get('tags', '[]')),
                "macros": parse_json_field(row.get('macros', '[]')),
                "inventory_mode": int(float(row.get('inventory_mode', 0))) if pd.notna(row.get('inventory_mode')) else 0,
                "inventory": parse_json_field(row.get('inventory', '{}'))
            })
    elif action == 'd':
        template_file = 'zabbix_template_delete.jinja2'
        host_id = row.get('host_id')
        if not host_id:
            logger.warning("Host ID is required for delete action. Skipping host '%s'.", row.get('host_name'))
            return
        try:
            data["host_id"] = int(float(host_id))  # Convert to integer
        except ValueError:
            logger.warning("Invalid Host ID '%s' for delete action. Skipping host '%s'.", host_id, row.get('host_name'))
            return
    elif action == 'm':
        template_file = 'zabbix_template_update.jinja2'
        data.update({
            "host_name": row.get('host_name', ''),
            "ip_address": row.get('ip_address', ''),
            "group_id": int(float(row.get('group_id', '0'))),
            "template_id": int(float(row.get('template_id', '0'))),
            "host_id": int(float(row.get('host_id', '0'))),
            "snmp_community": row.get('snmp_community', ''),
            "tags": parse_json_field(row.get('tags', '[]')),
            "macros": parse_json_field(row.get('macros', '[]')),
            "inventory_mode": int(float(row.get('inventory_mode', 0))) if pd.notna(row.get('inventory_mode')) else 0,
            "inventory": parse_json_field(row.get('inventory', '{}'))
        })
    else:
        logger.warning("Unknown action '%s' for host '%s'", action, row.get('host_name', 'Unknown'))
        return

    # Render JSON payload
    try:
        if template_file:
            template = env.get_template(template_file)
            json_payload = template.render(data)

            # Convert JSON payload to Python dict for validation
            json_payload_dict = json.loads(json_payload)
            
            # Print JSON payload in test mode or make request
            if test_mode:
                logger.info("Formatted JSON payload for test mode:")
                logger.info(json.dumps(json_payload_dict, indent=4))
            else:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(zabbix_url, headers=headers, data=json.dumps(json_payload_dict))
                logger.info("API response: %s", response.json())

            print("\n")
        else:
            logger.error("Template file not found for action '%s'", action)
    except Exception as e:
        logger.error("Error rendering template or making request: %s", e)

# Process each row in the DataFrame
for _, row in df.iterrows():
    process_row(row, test_mode=args.test)

logger.info("Process completed.")
