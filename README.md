# Azure Management Tool

The Azure Management Tool simplifies the management of essential Azure resources, providing an efficient way to handle AppSettings, SQL Server Firewall Rules and role-based access control (RBAC) for Azure subscriptions.

Built on the Azure REST API and Azure Identity SDK, this tool automates repetitive tasks such as fetching and saving configuration settings for Azure Web Apps, updating SQL firewall rules and ensuring that users have the correct permissions for resource management.

Key features include:
- **Azure Web App Configuration**: Fetch and store AppSettings and connection strings for your Azure Web Apps.
- **SQL Server Firewall Management**: Add or update firewall rules with ease, including automatic IP range calculations.
- **Subscription and Role Management**: Automatically manage role assignments and permissions, ensuring users have the correct roles to interact with Azure resources.

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
   "version": "vX.X.X",
   "app_name": "Azure Management Tool",
   "display_options": {
      "display_items_in_columns": true,
      "number_of_columns": 2
    },
   "role_options" : {
      "role_assignment_duration" : "PT30M"
    }
}
```

### Explanation:

- **version**: The version of the tool that is shown to users when the tool runs.
- **app_name**: The name of the application, which is used for display purposes.
- **display_options**:
  - **display_items_in_columns**: A boolean value (`true` or `false`) that controls whether to display items (like web apps or SQL servers) in multiple columns for better readability.
  - **number_of_columns**: Specifies how many columns to display when `display_items_in_columns` is set to `true`.
- **role_options**:
  - **role_assignment_duration**: Defines the duration for role assignments in ISO 8601 duration format (e.g., `PT30M` for 30 minutes, `PT1H` for 1 hour, `P1D` for 1 day). This allows the user to set the desired time duration for role assignments when they are automatically created.

## Usage

1. **Main Functionality**:

   Run the tool by executing the `main.py` file:
   ```bash
   python main.py
   ```

   You will be prompted to choose from the following actions:
   - **Create AppSettings**: Fetch and store app settings and connection strings for a selected Azure Web App.
   - **Add/Update SQL Firewall Rule**: Add or update a firewall rule for a selected SQL server.

2. **Web App Fetching (AppSettings)**:
   - The tool will fetch a list of available Azure Web Apps.
   - You can search for a web app by name or pick one from a list.
   - Once selected, the app settings and connection strings are fetched and saved to a JSON file.

3. **SQL Server Fetching (Firewall Rule)**:
   - The tool will fetch a list of SQL servers from your subscription.
   - You can search for a SQL server by name or select one from a list.
   - After selecting a SQL server, the tool fetches your current IP address and updates the firewall rule, or you can enter a custom IP.

4. **Authentication**:
   
   The tool uses Azure's `InteractiveBrowserCredential` for authentication. When running the tool, you will be prompted to authenticate via your browser.

5. **Role Management**:
   
   The tool automatically checks whether your user has the necessary role assignments for the selected subscription. If authorisation fails, it will attempt to create a role assignment with a default duration of 30 minutes and retry the operation.

## How to Use for Firewall

When using the tool to add or update SQL Firewall rules:

### Automatically Adds Your Name
- The tool will automatically use your authenticated username to create a firewall rule.

### Fetches Your Current IP Address
- It retrieves your current public IP address and automatically sets the IP range by default. For example, if your IP is `192.168.1.100`, the tool will set the IP range from `192.168.1.0` to `192.168.1.255`.

### Add for Someone Else
- If you'd like to add a firewall rule for someone else, you can simply provide their name and IP address. The tool will also calculate the correct IP range for the provided IP.

### SQL Server Fetching
- The tool will fetch all SQL servers within the subscription. You will be presented with a list of SQL servers or can refine the search by entering part of the server name.

### Example 1: Adding Your Own IP

When adding your own IP:

```bash
Please select a SQL server:
1. sql-server-1  
2. sql-server-2  
Enter the number of your choice: 1  

Adding IP to firewall rule: MyFirewallRule  
IP Range: 192.168.1.0 - 192.168.1.255  
Firewall rule 'MyFirewallRule' created/updated successfully.
```

### Example 2: Adding for Another Person

When adding for someone else:

```bash
Please select a SQL server:
1. sql-test  
2. sql-prod  
Enter the number of your choice: 1  

Enter the custom name: JohnDoe  
Enter the IP address: 10.0.0.25  

Adding IP to firewall rule: JohnDoeFirewallRule  
IP Range: 10.0.0.0 - 10.0.0.255  
Firewall rule 'JohnDoeFirewallRule' created/updated successfully.
```

## How to Use for AppSettings

When using the tool to fetch and store AppSettings:

### Web App Fetching
- The tool will connect to your Azure subscription and retrieve a list of available web apps.

### Select the Web App
- You will be presented with a list of web apps or can refine the search by entering part of the app name.

### Fetches AppSettings and Connection Strings
- Once a web app is selected, the tool will automatically fetch both the **app settings** and **connection strings** for that web app from Azure.

### Save Settings
- The fetched settings are saved in a structured JSON file for later use. The default location for the file is within the `results/` directory, and the file is named based on the web app's name.

### Example 1: Picking from List

When fetching AppSettings:

```bash
Please select a web app:
1. webapp1  
2. webapp2  
Enter the number of your choice: 1  

Fetching app settings for webapp1...  
Fetching connection strings for webapp1...  
Appsettings successfully saved to results/webapp1_appsettings.json
```

### Example 2: Searching by Name

When searching for a web app:

```bash
Enter the name (or part of the name) of the web app: api

Found 2 matching web apps:
1. api-test  
2. api-prod  
Enter more characters to refine search or the number of your choice: 1  

Fetching app settings for api-test...  
Fetching connection strings for api-test...  
Appsettings successfully saved to results/api-test_appsettings.json
```