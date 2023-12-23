# Script Migration Mule APIs to Kong APIs

## Description:
These script can be used to retrieve Mule policies, generate Kong plugins and push the data to a new branch on the API repos.

### Installation
```
pip install .
```

### Prepare API folder
The following script will create an apis folder with all the service from the samples_services.csv file:
- The -f parameter is used to specify the csv file with Mulesoft APIs name.
- The -e parameter is used to specify the environment id.
- The -w parameter is used to specify the weight of the ingress rules.
- The -p parameter is used to specify if we deploy the Ingress as main rules without Canary.

```
python prepareApisFolders.py -f samples_services.csv -e main -w 4
```

You will need to:
- retrieve a bearer_token for accessing CMA apis
- replace the organization_id and bearer in the script
- use the correct api_config_base_url in the script


### Push the API changes
You can then use the pushToGit.py script to push the changes to a new kong_canary_release branches.
```
python pushToGit.py
```

You will need to:
- check that you have the right to access CMA repository
- replace the git_base_url in the script


