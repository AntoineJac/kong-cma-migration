import argparse
import yaml
import json
import re
import os
from pathlib import Path

def extract_scopes_from_mandatory_custom_claims(mandatory_custom_claims):
    scopes = []
    scope_regex = re.compile(r'vars\.claimSet\.scope contains "(.*?):')

    for claim in mandatory_custom_claims:
        if claim.get("key") == "scope":
            scope_expression = claim.get("value", "")
            matches = scope_regex.findall(scope_expression)
            scopes.extend(matches)

    return scopes

def convert_to_kong_plugins(json_data, output_folder):
    kong_config = {"_format_version": "3.0", "plugins": []}
    created_files = []

    for policy in json_data.get("policyConfigurations", []):
        policy_data = policy.get("$self", {})
        asset_id = policy_data.get("assetId", "")

        if asset_id == "rate-limiting":
            method_regex = ""
            uri_template_regex = ""

            if policy_data.get("pointcutData") is not None:
                for pointcut_data in policy_data["pointcutData"]:
                    method_regex = pointcut_data.get("methodRegex", "")
                    uri_template_regex = pointcut_data.get("uriTemplateRegex", "")

            paths = uri_template_regex if uri_template_regex else []

            plugin_config = {
                "config": {
                    "limits": policy_data.get("configurationData", {}).get("rateLimits", [{}])[0].get("maximumRequests", 0),
                    "window_size": int(policy_data.get("configurationData", {}).get("rateLimits", [{}])[0].get("timePeriodInMilliseconds", 0) / 1000),
                    "hide_client_headers": True,
                    "strategy": "redis",
                    "sync_rate": 0.1,
                    "namespace": json_data.get("api", {}).get("$self", {}).get("assetId", "default-service") + "-namespace",
                    "identifier": "consumer",
                    "redis": {
                      "cluster_addresses":["{{KONG_KONNECT_PLUGIN_REDIS_HOST}}:{{KONG_KONNECT_PLUGIN_REDIS_PORT}}"],
                      "ssl": True
                    }
                },
                "enabled": not policy_data.get("disabled", False),
                "name": "rate-limiting-advanced",
                "service": json_data.get("api", {}).get("$self", {}).get("assetId", "default-service"),
            }

            if paths:
                plugin_config["route"] = paths

            kong_config["plugins"].append(plugin_config)
            file_name = f'{plugin_config["name"]}.yaml'
            created_files.append(file_name)
            # Write the plugin config to a separate YAML file
            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

        elif asset_id == "jwt-validation":
            mandatory_custom_claims = policy_data.get("configurationData", {}).get("mandatoryCustomClaims", [])
            scopes_required = extract_scopes_from_mandatory_custom_claims(mandatory_custom_claims)

            method_regex = ""
            uri_template_regex = ""

            if policy_data.get("pointcutData") is not None:
                for pointcut_data in policy_data["pointcutData"]:
                    method_regex = pointcut_data.get("methodRegex", "")
                    uri_template_regex = pointcut_data.get("uriTemplateRegex", "")

            plugin_config = {
                "config": {
                    "scopes_required": scopes_required,
                    "auth_methods": ["bearer"],
                    "issuer": "{{KONG_KONNECT_PLUGIN_OIDC_ISSUER_URL}}",
                    "extra_jwks_uris": ["{{KONG_KONNECT_PLUGIN_OIDC_EXTRA_JWKS_URIS}}"],
                    "verify_signature": True,
                    "anonymous": "anonymous",
                    "consumer_optional": False,
                    "consumer_claim": ["username"],
                },
                "enabled": not policy_data.get("disabled", False),
                "name": "openid-connect",
                "service": json_data.get("api", {}).get("$self", {}).get("assetId", "default-service"),
            }

            kong_config["plugins"].append(plugin_config)
            file_name = f'{plugin_config["name"]}.yaml'
            created_files.append(file_name)
            # Write the plugin config to a separate YAML file
            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

        elif asset_id == "client-id-enforcement":
            plugin_config = {
                "config": {
                    "aws_sm_service_key": json_data.get("api", {}).get("$self", {}).get("assetId", "default-service"),
                    "token_ttl": 300,
                },
                "enabled": not policy_data.get("disabled", False),
                "name": "mulesoft-mediation",
                "service": [json_data.get("api", {}).get("$self", {}).get("assetId", "default-service")],
            }

            kong_config["plugins"].append(plugin_config)
            file_name = f'{plugin_config["name"]}.yaml'
            created_files.append(file_name)
            # Write the plugin config to a separate YAML file
            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

    return kong_config, created_files

def main():
    parser = argparse.ArgumentParser(description='Convert JSON to YAML and create plugin files.')
    parser.add_argument('-f', '--file-name', required=True, help='JSON file to convert')
    parser.add_argument('-o', '--output-folder', default='plugins', help='Output folder for YAML files (default: plugins)')

    args = parser.parse_args()

    json_file = args.file_name
    output_folder = args.output_folder

    # Ensure the output folder exists
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    with open(json_file, 'r') as file:
        json_data = json.load(file)

    kong_config, files_created = convert_to_kong_plugins(json_data, output_folder)

    print(f"Conversion completed.\nTotal files created: {len(files_created)}")

    for file_name in files_created:
        print(file_name)

if __name__ == "__main__":
    main()
