# OrgBranchProtector
This web app listens for repository creation events and sets protections for default branch.

## Notes
* This is a test application. It is not recommended to use it on existing organization. You may want to create empty/dummy organization.
* After authorization the app generates webhook path. Webhook contains GitHub API access_token so you may want to treat it as password
* All org admins will be able to see created webhook (and access_token as a result)
* Application does not store any data
* It is recommended to revoke access after testing (Settings->Applications->Authorized OAuth Apps->ghBranchProtector)

## How to use
* [Authorize](https://ghbranchprotector.azurewebsites.net/authorize) the app
* Copy generated webhook URL
* Create new webhook inside of your organization:
    * Org->Settings->Webhook->Add Webhook
    * Paste webhook URL
    * Set content type to "application/json"
    * Select "Let me select individual events."
    * Check "Repositories"
    * Your done. Click "Update webhook"
* Create new repository inside your organization
* Application will automatically setup default branch protection and create issue outlining settings

## Exemplary organization
Take a look at [rekoHub](https://github.com/rekoHub) to see app in action.

## Deploy web app to Azure
Follow [this](https://docs.microsoft.com/en-us/azure/app-service/containers/quickstart-python?toc=%2Fpython%2Fazure%2FTOC.json&tabs=bash) guide if you want to deploy web app to your Azure account.
