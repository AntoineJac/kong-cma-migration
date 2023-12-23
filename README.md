The following script will create an apis folder with all the service from the samples_services.csv file.
The e parameter is used to specify the environment id.
The w parameter is used to specify the weight of the ingress rules.

```
python prepareApisFolders.py -f samples_services.csv -e main -w 4
```

You can then use the pushToGit.py script to push the changes to a new kong_canary_release branches.
```
python pushToGit.py
```

You will need to:
- retrieve a bearer_token for accessing CMA apis
- uncomment line 61 and 63 in the prepareApisFolders.py script
- use correct organization_id and bearer line 93 and 94

