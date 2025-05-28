#!/bin/bash

# Read the keyVaultName from settings.json
KEY_VAULT_NAME=$(grep '"keyVaultName"' .azure/settings.json | cut -d'"' -f4)

if [ -z "$KEY_VAULT_NAME" ]; then
    echo "Error: Could not read keyVaultName from settings.json"
    exit 1
fi

echo "Listing secrets from Key Vault: $KEY_VAULT_NAME"
# List all secrets from the Key Vault
az keyvault secret list --vault-name "$KEY_VAULT_NAME" --query "[].name" -o tsv | while read -r secret_name; do
    echo "Secret: $secret_name"
    echo "Value: $(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "$secret_name" --query "value" -o tsv)"
done 