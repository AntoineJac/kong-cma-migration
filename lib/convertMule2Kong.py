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

def add_default_plugins(service_name, output_folder):
    added_files = []

    plugin_config = {
        "name": "proxy-cache-advanced",
        "service": service_name,
        "enabled": False,
        "config": {
            "cache_ttl": 300,
            "storage_ttl": 300,
            "response_code": [200],
            "request_method": ["GET", "HEAD"],
            "content_type": ["text/plain", "application/json", "application/json; charset=utf-8", "text/plain; charset=UTF-8"],
            "strategy": "redis",
            "redis": {
                "cluster_addresses": ["{{KONG_KONNECT_PLUGIN_REDIS_HOST}}:{{KONG_KONNECT_PLUGIN_REDIS_PORT}}"],
                "ssl": True
            }
        }
    }

    file_name = f'{plugin_config["name"]}.yaml'
    with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
        yaml.dump(plugin_config, plugin_file, default_flow_style=False)

    added_files.append(file_name)

    return added_files

def convert_to_kong_plugins(json_data, output_folder):
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    kong_config = {"_format_version": "3.0", "plugins": []}
    service_name = json_data.get("api", {}).get("$self", {}).get("assetId", "default-service")
    converted_files = []
    unknown_policies = []

    added_files = add_default_plugins(service_name, output_folder)

    for policy in json_data.get("policyConfigurations", []):
        policy_data = policy.get("$self", {})
        asset_id = policy_data.get("assetId", "")

        if asset_id == "rate-limiting":
            method_regex, uri_template_regex = "", ""

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
                    "namespace": f'{service_name}-namespace',
                    "identifier": "consumer",
                    "redis": {
                        "cluster_addresses": ["{{KONG_KONNECT_PLUGIN_REDIS_HOST}}:{{KONG_KONNECT_PLUGIN_REDIS_PORT}}"],
                        "ssl": True
                    }
                },
                "enabled": not policy_data.get("disabled", False),
                "name": "rate-limiting-advanced",
                "service": service_name,
            }

            if paths:
                plugin_config["route"] = paths

            file_name = f'{plugin_config["name"]}.yaml'
            converted_files.append(file_name)

            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

        elif asset_id == "jwt-validation":
            mandatory_custom_claims = policy_data.get("configurationData", {}).get("mandatoryCustomClaims", [])
            scopes_required = extract_scopes_from_mandatory_custom_claims(mandatory_custom_claims)

            method_regex, uri_template_regex = "", ""

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
                "service": service_name,
            }

            file_name = f'{plugin_config["name"]}.yaml'
            converted_files.append(file_name)

            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

        elif asset_id == "basic-auth-simple":
            plugin_config = {
                "config": {"hide_credentials": True},
                "enabled": not policy_data.get("disabled", False),
                "name": "basic-auth",
                "service": service_name,
            }

            file_name = f'{plugin_config["name"]}.yaml'
            converted_files.append(file_name)

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
                "service": service_name,
            }

            file_name = f'{plugin_config["name"]}.yaml'
            converted_files.append(file_name)

            with open(os.path.join(output_folder, file_name), 'w') as plugin_file:
                yaml.dump(plugin_config, plugin_file, default_flow_style=False)

        else:
            print(f"Unknown asset ID: {asset_id}")
            unknown_policies.append(asset_id)

    api_policies = json_data.get("policyConfigurations", [])

    print(f"> Conversion completed.\nNumber of Policies: {len(api_policies)}")
    print(f"Total policies converted: {len(converted_files)}\nNumber of unmapped Policies: {len(unknown_policies)}")
    print(f"Number of added Plugins: {len(added_files)}\nTotal files created: {len(converted_files + added_files)}")

    print(f"Unmapped policies:")
    for file_name in unknown_policies:
        print(f"     {file_name}")

    print(f"Plugins created:")
    for file_name in converted_files + added_files:
        print(f"     {file_name}")

    result = {
        "status": "success" if len(converted_files) == len(api_policies) else "failure",
        "api_id": service_name,
        "policies_count": len(api_policies),
        "plugins_converted": len(converted_files),
        "plugins_added": len(added_files),
        "plugins_total": len(converted_files + added_files),
        "unknown_policies": unknown_policies,
    }

    return result

def main():
    parser = argparse.ArgumentParser(description='Convert JSON to YAML and create plugin files.')
    parser.add_argument('-f', '--file-name', required=True, help='JSON file to convert')
    parser.add_argument('-o', '--output-folder', default='plugins', help='Output folder for YAML files (default: plugins)')

    args = parser.parse_args()

    json_file = args.file_name
    output_folder = args.output_folder

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    with open(json_file, 'r') as file:
        json_data = json.load(file)

    result = convert_to_kong_plugins(json_data, output_folder)

    print_conversion_result(result)

    return result

def print_conversion_result(result):
    status = result["status"]
    api_id = result["api_id"]
    plugins_converted = result["plugins_converted"]
    policies_count = result["policies_count"]

    if status == "success":
        print(f"> Successful_api api_id: {api_id}, plugins_converted: {plugins_converted}, policies_count: {policies_count}")
    else:
        print(f"> Unsuccessful_api api_id: {api_id}, plugins_converted: {plugins_converted}, policies_count: {policies_count}")
        print(f"> Error Message: {result['error_message']}")

if __name__ == "__main__":
    main()
