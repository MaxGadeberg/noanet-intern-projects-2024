# NoaNet Internship Projects 2024

Projects I worked on during my internship from June 24th, 2024 to August 30th, 2024. Below is a brief overview of the various projects and their respective files.

## Project Structure

The projects are organized into the following directories:

### `./downdetector` - Downdetector Scripts

Scripts for monitoring website status using Downdetector.

- **`downdetector-testing.ipynb`**: Testing and backup notebook for Downdetector.
- **`downdetector.ipynb`**: Script to detect the status of a list of sites on Downdetector.com.
- **`downdetectorcorp.ipynb`**: Script to detect the status of specific corporate websites.

### `./host-generator` - Zabbix Host Importer/Generator

Tools for importing and generating Zabbix hosts.

- **`./templates`**: Jinja templates for Zabbix request configurations.
- **`hostexample.csv`**: Example CSV file(s) for importing into Zabbix.
- **`script.py`**: Script to read from CSV files and import data into Zabbix.

### `./selenium` - Selenium Web Scraping and Testing

Scripts for testing and web scraping using Selenium.

- **`snow_business_service.py`**: Web scrape and test the ServiceNow (SNOW) business service creation page.
- **`snow_case.py`**: Web scrape and test the SNOW case creation page.
- **`snow_change_request.py`**: Web scrape and test the SNOW change request creation page.
- **`snow_incident.py`**: Web scrape and test the SNOW incident creation page.
- **`snow_login.py`**: Web scrape and test the SNOW login functionality.
- **`tests.py`**: Selenium testing script for various selectors.

### `./zabbix-snow` - Zabbix and ServiceNow (SNOW) Integration

Scripts for integrating and managing data between Zabbix and ServiceNow.

- **`add-modify.py`**: Pulls data from SNOW and adds, modifies, or drops entries in Zabbix.
- **`addingtozabbix.ipynb`**: Imports data into Zabbix from a CSV file.
- **`addtags.py`**: Adds specified tags to hosts in Zabbix.
- **`dnsnameupdater.ipynb`**: Updates DNS names in Zabbix.
- **`dnsrecords.ipynb`**: Generates a CSV report of all hosts in Zabbix.
- **`gethosts.py`**: Searches for hosts in Zabbix and creates a CSV report.
- **`maintenance`**: Updates maintenance periods in Zabbix based on data from SNOW.
- **`missinghosts.py`**: Compares a CSV file to Zabbix and identifies missing hosts, writing the results to a new CSV file.
- **`snowincidents.ipynb`**: Charts SNOW incidents for analysis.
