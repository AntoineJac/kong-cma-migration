import csv
import os
import shutil
import requests
import argparse
import json
from lib.convertMule2Kong import convert_to_kong_plugins

def create_folders_from_csv(csv_file, organization_id, environment_id, bearer_token, canary_weight):
    apis_folder_path = os.path.join(os.getcwd(), 'apis')
    os.makedirs(apis_folder_path, exist_ok=True)

    successful_apis = []
    unsuccessful_apis = []

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            api_name = row['apiName']
            print(f"\nSTART THE CONVERSION OF THE API: {api_name}")
            result = create_folder(api_name, organization_id, environment_id, bearer_token, apis_folder_path, canary_weight)

            if result.get("status") == "success":
                successful_apis.append(result)
            else:
                unsuccessful_apis.append(result)

    print_conversion_summary(successful_apis, unsuccessful_apis)

def create_folder(api_name, organization_id, environment_id, bearer_token, apis_folder_path, canary_weight):
    folder_path = os.path.join(apis_folder_path, api_name)
    os.makedirs(folder_path, exist_ok=True)

    konnect_template_dest = os.path.join(folder_path, 'konnect')
    if os.path.exists(konnect_template_dest):
        shutil.rmtree(konnect_template_dest)

    konnect_template_src = os.path.join(os.getcwd(), 'konnect_template')
    shutil.copytree(konnect_template_src, konnect_template_dest)

    ingress_file_path = os.path.join(konnect_template_dest, 'ingressRules', 'kong-proxy-ingress-api-canary.yaml')
    update_canary_weight(ingress_file_path, canary_weight)

    download_api_config(api_name, folder_path, organization_id, environment_id, bearer_token)

    convert_script_path = os.path.join(os.getcwd(), 'convertMule2Kong.py')
    config_file_path = os.path.join(folder_path, f'{api_name}_config.json')

    plugins_folder_path = os.path.join(folder_path, 'konnect', 'plugins')
    with open(config_file_path, 'r') as file:
        json_data = json.load(file)

    result = convert_to_kong_plugins(json_data, plugins_folder_path)

    return result

def update_canary_weight(ingress_file_path, canary_weight):
    with open(ingress_file_path, 'r') as ingress_file:
        file_content = ingress_file.read()

    updated_content = file_content.replace('nginx.ingress.kubernetes.io/canary-weight: "1"', f'nginx.ingress.kubernetes.io/canary-weight: "{canary_weight}"')

    with open(ingress_file_path, 'w') as ingress_file:
        ingress_file.write(updated_content)

def download_api_config(api_name, folder_path, organization_id, environment_id, bearer_token):
    api_config_url = f'https://raw.githubusercontent.com/AntoineJac/kong-cma-migration/{environment_id}/examples/{api_name}.json'
    headers = {}

    #https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{organization_id}/environments/{environment_id}/apis/{api_name}/config
    # {'Authorization': f'Bearer {bearer_token}'}

    response = requests.get(api_config_url, headers=headers)

    if response.status_code == 200:
        config_file_path = os.path.join(folder_path, f'{api_name}_config.json')
        with open(config_file_path, 'wb') as config_file:
            config_file.write(response.content)
        print(f"> Configuration file for {api_name} downloaded successfully.")
    else:
        print(f"> Failed to download configuration for {api_name}. Status code: {response.status_code}")

def print_conversion_summary(successful_apis, unsuccessful_apis):
    print(f"\n\nSUMMARY:")
    print("\n---------------- Successful APIs -----------------")
    for result in successful_apis:
        api_name = result["api_id"]
        policies_count = result["policies_count"]
        plugins_converted = result["plugins_converted"]
        plugins_added = result["plugins_added"]
        plugins_total = result["plugins_total"]

        print(f"\n{api_name}")
        print(f"      Policies Count: {policies_count}")
        print(f"      Plugins Converted: {plugins_converted}")
        print(f"      Plugins Added: {plugins_added}")
        print(f"      Total Plugins Added: {plugins_total}")

    print("\n---------------- Unsuccessful APIs -----------------")
    for result in unsuccessful_apis:
        api_name = result["api_id"]
        unknown_policies = result["unknown_policies"]
        print(f"\n{api_name}")
        print(F"      Error: Impossible to convert the following policies - check mapping: {unknown_policies}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create folders and download API configuration.')
    parser.add_argument('-f', '--file-name', required=True, help='CSV file containing API data')
    parser.add_argument('-e', '--environment', required=True, help='Your environment ID')
    parser.add_argument('-w', '--weight', required=True, help='Canary release weight')

    args = parser.parse_args()

    csv_file_path = args.file_name
    environment_id = args.environment
    canary_weight = args.weight
    organization_id = 'your_organization_id'  # Replace with your actual organization ID
    bearer_token = 'your_bearer_token'  # Replace with your actual Bearer Token

    create_folders_from_csv(csv_file_path, organization_id, environment_id, bearer_token, canary_weight)
