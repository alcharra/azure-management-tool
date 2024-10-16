# Azure Management Tool

This tool allows you to manage Azure AppSettings, SQL Firewall Rules and Azure Subscriptions using the Azure REST API and Azure Identity SDK.

## Features

- **AppSettings Management**: Fetch and store app settings and connection strings for Azure Web Apps.
- **SQL Firewall Rule Management**: Add or update firewall rules for SQL servers in Azure.
- **Subscription and Role Management**: Manage role assignments and eligibilities for subscriptions and ensure the correct roles are activated for users.

## Requirements

- Python 3.8+
- Azure Identity SDK
- JWT (for token decoding)
- Requests library (for making HTTP calls)

## Installation

1. Clone this repository.
2. Install dependencies using `pip`:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you have valid Azure credentials and access to the necessary subscriptions.

## Configuration (Example)

The tool expects a `config.json` file structured like this:

```json
{
    "Environment 1": {
        "Subscription Name 1": {
            "resourceGroupName": [
                "your-resource-group-1",
                "your-resource-group-2"
            ]
        },
        "Subscription Name 2": {
            "resourceGroupName": [
                "your-resource-group-3"
            ]
        }
    },
    "Environment 2": {
        "Subscription Name 3": {
            "resourceGroupName": []
        }
    }
}
```

### Explanation:

- Each environment (e.g., `Development`, `Pre-production`) contains multiple subscriptions.
- For each subscription, the key `resourceGroupName` represents an array of resource groups associated with that subscription.
- **Empty `resourceGroupName`**: If the `resourceGroupName` is an empty array (e.g., `[]`), the tool will still work and the functionality will process all available resources for that subscription.
- You can add as many subscriptions as necessary within each environment.

This flexibility allows you to specify which resource groups you want to target or leave the array empty to target all available resource groups within a subscription.

## Usage

1. **Main Functionality**:

   Run the tool by executing the `main.py` file:
   ```bash
   python main.py
   ```

   You will be prompted to select an environment and subscription and then choose an action:
   - **Create AppSettings**: Fetch and store app settings and connection strings for a selected Azure Web App.
   - **Add/Update SQL Firewall Rule**: Add or update a firewall rule for a selected SQL server.

2. **Authentication**:
   
   The tool uses Azure's `InteractiveBrowserCredential` for authentication. You will be prompted to authenticate with Azure when running the tool.

3. **Role Management**:
   
   The tool automatically checks if your current user has the necessary role assignments for a subscription. If not, it will create a new role assignment.

## How to Use for Firewall

When using the tool to add or update SQL Firewall rules:

- **Automatically adds your name**: The tool will automatically use your authenticated user name to create a firewall rule.
- **Fetches your current IP address**: It retrieves your current public IP address and automatically sets the IP range by default. For example, if your IP is `192.168.1.100`, the tool will set the IP range from `192.168.1.0` to `192.168.1.255`.
- **Add for someone else**: If you'd like to add a firewall rule for someone else, you can simply provide their name and IP address. The tool will also calculate the correct IP range for the provided IP.
- **SQL Server Fetching**:
  - If `resourceGroupName` is **not empty**, the tool will fetch all SQL servers from the provided resource groups.
  - If `resourceGroupName` is **empty**, the tool will fetch all SQL servers within the subscription.

### Example

- When adding your own IP:
    ```bash
    Adding IP to firewall rule: MyFirewallRule
    IP Range: 192.168.1.0 - 192.168.1.255
    ```

- When adding for another person:
    ```bash
    Enter the custom name: JohnDoe
    Enter the IP address: 10.0.0.25
    Adding IP to firewall rule: JohnDoeFirewallRule
    IP Range: 10.0.0.0 - 10.0.0.255
    ```

## How to Use for AppSettings

When using the tool to fetch and store AppSettings:

- **Web App Fetching**:
If `resourceGroupName` is **not empty**, the tool will fetch all web apps within the specified resource groups.
If `resourceGroupName` is **empty**, the tool will fetch all web apps within the subscription.
- **Select the Web App**: After fetching the web apps, you will be prompted to select one from a list.
- **Fetches AppSettings and Connection Strings**: The tool will automatically fetch both the app settings and connection strings for the selected web app.
- **Save Settings**: The fetched settings are saved in a JSON file for later use.

### Example

- When fetching AppSettings:
    ```bash
    Please select a web app:
    1. webapp1 (Resource Group: resourceGroup1)
    2. webapp2 (Resource Group: resourceGroup1)
    Enter the number of your choice: 1
    Fetching app settings for webapp1...
    Settings saved to results/webapp1_appsettings.json
    ```