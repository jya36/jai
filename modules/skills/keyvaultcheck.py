from azure.identity import AzureCliCredential
from azure.mgmt.keyvault import KeyVaultManagementClient

def getConfig(akvName,subscription):
    credential = AzureCliCredential()
    akvClient = KeyVaultManagementClient(credential,subscription)
    akv = akvClient.vaults.list()

    vaultId = ''
    for vault in akv:
        if vault.name == akvName:
            vaultId = vault.id
            break
    vaultId = vaultId.split('/')
    akv = akvClient.vaults.get(vaultId[4],vaultId[8])
    return akv.properties

