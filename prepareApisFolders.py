import csv
import os
import sys
import shutil
import requests
import subprocess
import argparse

def create_folders_from_csv(csv_file, organization_id, environment_id, bearer_token, canary_weight):
    # Create the 'apis' folder if it doesn't exist
    apis_folder_path = os.path.join(os.getcwd(), 'apis')
    os.makedirs(apis_folder_path, exist_ok=True)

    with open(csv_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            api_name = row['apiName']
            create_folder(api_name, organization_id, environment_id, bearer_token, apis_folder_path, canary_weight)

def create_folder(api_name, organization_id, environment_id, bearer_token, apis_folder_path, canary_weight):
    # Create a folder with the name of the apiName inside the 'apis' folder
    folder_path = os.path.join(apis_folder_path, api_name)
    os.makedirs(folder_path, exist_ok=True)

    # Clear the destination directory if it already exists
    konnect_template_dest = os.path.join(folder_path, 'konnect')
    if os.path.exists(konnect_template_dest):
        shutil.rmtree(konnect_template_dest)

    # Copy the 'konnect_template' folder to the newly created folder
    konnect_template_src = os.path.join(os.getcwd(), 'konnect_template')
    shutil.copytree(konnect_template_src, konnect_template_dest)

    # Modify the ingress YAML file with the provided canary weight
    ingress_file_path = os.path.join(konnect_template_dest, 'ingressRules', 'kong-proxy-ingress-api-canary.yaml')
    update_canary_weight(ingress_file_path, canary_weight)

    # Download configuration file and save it to the folder
    download_api_config(api_name, folder_path, organization_id, environment_id, bearer_token)

    # Call convert.py for each API configuration file
    convert_script_path = os.path.join(os.getcwd(), 'convertMule2Kong.py')
    config_file_path = os.path.join(folder_path, f'{api_name}_config.json')
    call_convert_script(convert_script_path, config_file_path, folder_path)

def update_canary_weight(ingress_file_path, canary_weight):
    # Read the content of the ingress file
    with open(ingress_file_path, 'r') as ingress_file:
        file_content = ingress_file.read()

    # Update the canary weight in the content
    updated_content = file_content.replace('nginx.ingress.kubernetes.io/canary-weight: "1"', f'nginx.ingress.kubernetes.io/canary-weight: "{canary_weight}"')

    # Write the updated content back to the file
    with open(ingress_file_path, 'w') as ingress_file:
        ingress_file.write(updated_content)


def download_api_config(api_name, folder_path, organization_id, environment_id, bearer_token):
    api_config_url = f'https://raw.githubusercontent.com/AntoineJac/kong-cma-migration/{environment_id}/examples/{api_name}.json'
    # https://anypoint.mulesoft.com/apimanager/api/v1/organizations/{organization_id}/environments/{environment_id}/apis/{api_name}/config
    headers = {}
    # {'Authorization': f'Bearer {bearer_token}'}
    
    response = requests.get(api_config_url, headers=headers)

    if response.status_code == 200:
        config_file_path = os.path.join(folder_path, f'{api_name}_config.json')
        with open(config_file_path, 'wb') as config_file:
            config_file.write(response.content)
        print(f"Configuration file for {api_name} downloaded successfully.")
    else:
        print(f"Failed to download configuration for {api_name}. Status code: {response.status_code}")

def call_convert_script(script_path, config_file_path, output_folder):
    # Call convert.py script with the API configuration file and output folder as parameters
    python_executable = sys.executable
    # Specify the path to the 'konnect/plugins' folder within the API folder
    plugins_folder_path = os.path.join(output_folder, 'konnect', 'plugins')
    subprocess.run([python_executable, script_path, '-f', config_file_path, '-o', plugins_folder_path])

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
