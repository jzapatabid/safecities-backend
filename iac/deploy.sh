az login

az deployment group validate --resource-group rg-d-safecities --subscription "Sinapsis Azure Dev/Test" --template-file vmtemplate.json --parameters vmtemplate.parameters.json

az deployment group create --mode Incremental --name safecities001 --resource-group rg-d-safecities --subscription "Sinapsis Azure Dev/Test" --template-file vmtemplate.json --parameters vmtemplate.parameters.json

