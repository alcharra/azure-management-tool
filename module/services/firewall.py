import requests
import json

class SQLFirewallRuleManager:

    def __init__(self, subscription_id, token, firewall_name, resource_groups):
        self.subscription_id = subscription_id
        self.base_url = "https://management.azure.com"
        self.api_version = "2021-11-01"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.firewall_name = firewall_name
        self.server_name = None
        self.ip_address = None
        self.resource_groups = [rg.lower() for rg in resource_groups]
        
    def list_sql_servers(self):
        # https://learn.microsoft.com/en-us/rest/api/sql/servers/list?view=rest-sql-2021-11-01
        url = (
            f"{self.base_url}/subscriptions/{self.subscription_id}/"
            f"providers/Microsoft.Sql/servers?api-version={self.api_version}"
        )
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                servers = response.json().get("value", [])
                if not servers:
                    print("No SQL servers found in the subscription.")
                    return None
                for server in servers:
                    server['resourceGroup'] = self.extract_resource_group(server['id']).lower()
                if self.resource_groups:
                    filtered_servers = [
                        server for server in servers if server['resourceGroup'] in self.resource_groups
                    ]
                    if not filtered_servers:
                        print("No matching resource groups found. Displaying all SQL servers.")
                    return filtered_servers if filtered_servers else servers
                else:
                    return servers
            else:
                print(f"Failed to list SQL servers. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error occurred while listing SQL servers: {e}")
            return None
        
    def extract_resource_group(self, server_id):
        return server_id.split("/")[4]  # Resource group is the 5th element in the id path
    
    def select_sql_server(self):
        all_servers = self.list_sql_servers()
        if not all_servers:
            print("No SQL servers found in the subscription.")
            return None
        # Display all available servers
        print("\nPlease select a SQL server:")
        for i, server in enumerate(all_servers, start=1):
            resource_group = self.extract_resource_group(server['id'])
            print(f"{i}. {server['name']} (Resource Group: {resource_group})")
        selected_index = int(input("Enter the number of the SQL server you want to select: ")) - 1
        if 0 <= selected_index < len(all_servers):
            selected_server = all_servers[selected_index]
            self.server_name = selected_server['name']
            resource_group = self.extract_resource_group(selected_server['id'])
            return selected_server['name'], resource_group
        else:
            print("Invalid selection.")
            return None, None
        
    def get_public_ipv4(self):
        try:
            # https://geo.ipify.org/docs
            response = requests.get("https://api.ipify.org?format=json")
            if response.status_code == 200:
                self.ip_address = response.json()["ip"]
                return self.ip_address
            else:
                print(f"Failed to fetch public IP. Status Code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching public IP: {e}")
            return None
        
    def calculate_ip_range(self, ipv4):
        if not ipv4:
            return None, None
        ip_parts = ipv4.split('.')
        start_ip = '.'.join(ip_parts[:3] + ['0'])
        end_ip = '.'.join(ip_parts[:3] + ['255'])
        return start_ip, end_ip
    
    def prompt_firewall_rule_name(self):
        user_input = input(f"\nEnter a new firewall rule name or press Enter to use '{self.firewall_name}': ").strip()
        return user_input if user_input else self.firewall_name
        
    def prompt_ip_address(self):
        user_input = input(f"\nEnter a custom IPv4 address or press Enter to use your current public IP ({self.ip_address}): ").strip()
        return user_input if user_input else self.ip_address
    
    def create_or_update_firewall_rule(self):
        if not self.server_name:
            selected_server, selected_resource_group = self.select_sql_server()
            if not selected_server:
                print("No SQL server selected. Aborting operation.")
                return None
        firewall_rule_name = self.prompt_firewall_rule_name()
        print(f"Adding IP to firewall rule: {firewall_rule_name}")
        if not self.ip_address:
            self.get_public_ipv4()
        if not self.ip_address:
            print("Could not fetch public IPv4 address. Aborting.")
            return None
        ip_address = self.prompt_ip_address() if firewall_rule_name != self.firewall_name else self.ip_address
        if not ip_address:
            print("Invalid IP address. Aborting.")
            return None
        start_ip, end_ip = self.calculate_ip_range(ip_address)
        if not start_ip or not end_ip:
            print("Invalid IP range. Aborting.")
            return None
        print(f"IP Range: {start_ip} - {end_ip}")
        # https://learn.microsoft.com/en-us/rest/api/sql/firewall-rules/create-or-update?view=rest-sql-2021-11-01
        url = (
            f"{self.base_url}/subscriptions/{self.subscription_id}/"
            f"resourceGroups/{selected_resource_group}/"
            f"providers/Microsoft.Sql/servers/{self.server_name}/"
            f"firewallRules/{firewall_rule_name}?api-version={self.api_version}"
        )
        body = {
            "properties": {
                "startIpAddress": start_ip,
                "endIpAddress": end_ip
            }
        }
        response = requests.put(url, headers=self.headers, data=json.dumps(body))
        if response.status_code in (200, 201):
            print(f"Firewall rule '{firewall_rule_name}' created/updated successfully.")
        else:
            print(f"Failed to create/update firewall rule '{firewall_rule_name}'. Status Code: {response.status_code}, Response: {response.text}")
        return response