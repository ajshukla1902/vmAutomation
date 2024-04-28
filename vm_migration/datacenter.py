#!/usr/local/bin/python3
import yaml
import requests
from requests.auth import HTTPBasicAuth
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# API information
api_url = 'url/rest'
api_user = 'username'
api_pass = 'password'

# Main function to initiate API call
def main():
    # Disable SSL warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # Call function to get vCenter cluster status
    get_vcenter_cluster_status()

# Function to get vCenter cluster status
def get_vcenter_cluster_status():
    # Call API to get data about vCenter datacenter
    resp = get_api_data('{}/vcenter/datacenter'.format(api_url))
    # Uncomment below line if you want to print the raw response content
    #print(resp.content)
    # Extract JSON from response content
    j = resp.content
    # Print the JSON data
    print(format(j))

# Function to authenticate with vCenter
def auth_vcenter(username, password):
    # API call to authenticate and get session ID
    resp = requests.post('{}/com/vmware/cis/session'.format(api_url), auth=(api_user, api_pass), verify=False)
    if resp.status_code != 200:
        print('Error! API responded with: {}'.format(resp.status_code))
        return
    # Extract and return the session ID
    return resp.json()['value']

# Function to make API requests with authentication
def get_api_data(req_url):
    # Authenticate to get session ID
    sid = auth_vcenter(api_user, api_pass)
    # Make API request with session ID in header
    resp = requests.get(req_url, verify=False, headers={'vmware-api-session-id': sid})
    if resp.status_code != 200:
        print('Error! API responded with: {}'.format(resp.status_code))
        return
    # Return the response
    return resp

# Call the main function to start the script
main()
