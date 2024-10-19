# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
from typing import Optional, Tuple, List, Dict, Any

# IMPORT UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////
from module.utils import *

# SQL FIREWALL RULE MANAGER CLASS
# ///////////////////////////////////////////////////////////////
class SQLFirewallRuleManager:

    # INITIALISE FIREWALL RULE MANAGER
    # ///////////////////////////////////////////////////////////////
    def __init__(self, subscription: Dict[str, str], token: str, firewall_name: str, subscription_manager: Any) -> None:
        self.subscription_manager: Any = subscription_manager
        self.subscription: Dict[str, str] = subscription
        self.base_url: str = "https://management.azure.com"
        self.api_version: str = "2021-11-01"
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.firewall_name: str = firewall_name
        self.server_name: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.list_sql_servers: Optional[List[Dict[str, Any]]] = self.list_sql_servers()

    # LIST SQL SERVERS
    # API Reference: https://learn.microsoft.com/en-us/rest/api/sql/servers/list?view=rest-sql-2021-11-01
    # ///////////////////////////////////////////////////////////////
    def list_sql_servers(self) -> Optional[List[Dict[str, Any]]]:
        url: str = (
            f"{self.base_url}/subscriptions/{self.subscription['subscriptionId']}/"
            f"providers/Microsoft.Sql/servers?api-version={self.api_version}"
        )

        response = make_api_request(
            url=url,
            method="GET",
            headers=self.headers,
            retry_callback=self.list_sql_servers,
            create_role_assignment= self.subscription_manager.create_role_assignment,
            subscription = self.subscription
        )

        if isinstance(response, dict):
            sql_servers: List[Dict[str, Any]] = response.get("value", [])
        elif isinstance(response, list):
            sql_servers: List[Dict[str, Any]] = response
        else:
            print("Unexpected response format. Returning None.")
            return None

        if not sql_servers:
            print("No SQL servers found in the subscription.")
            return None

        for server in sql_servers:
            server['resourceGroup'] = extract_segment(server['id'], 4).lower()

        return sql_servers

    # SELECT SQL SERVER
    # Allows user to select a SQL server via search or list selection
    # ///////////////////////////////////////////////////////////////
    def select_sql_server(self) -> Optional[Tuple[str, str]]:
        if not self.list_sql_servers:
            print("No SQL servers found in the subscription.")
            return None

        print("\nWould you like to:")
        print("1. Search for a SQL server by name")
        print("2. Pick from a list of SQL servers")
        user_choice = input("Enter 1 to search or 2 to pick from list: ").strip()

        if user_choice == "1":
            search_term = input("Enter the name (or part of the name) of the SQL server: ").lower()
            matching_servers: List[Dict[str, Any]] = [server for server in self.list_sql_servers if search_term in server['name'].lower()]

            while len(matching_servers) > 1:
                print(f"\nFound {len(matching_servers)} matching SQL servers.")
                for i, server in enumerate(matching_servers, start=1):
                    print(f"{i}. {server['name']}")

                refine_choice = input("\nEnter more characters to refine search or the number of your choice: ").strip()

                if refine_choice.isdigit():
                    selected_index = int(refine_choice) - 1
                    if 0 <= selected_index < len(matching_servers):
                        selected_server = matching_servers[selected_index]
                        self.server_name = selected_server['name']
                        resource_group = extract_segment(selected_server['id'], 4)
                        return selected_server['name'], resource_group
                    else:
                        print("Invalid selection. Please enter a valid number.")
                else:
                    search_term = refine_choice.lower()
                    matching_servers = [server for server in self.list_sql_servers if search_term in server['name'].lower()]

            if len(matching_servers) == 1:
                selected_server = matching_servers[0]
                self.server_name = selected_server['name']
                resource_group = extract_segment(selected_server['id'], 4)
                return selected_server['name'], resource_group
            else:
                print("No matching SQL servers found.")
                return None

        elif user_choice == "2":
            print("\nPlease select a SQL server from the list:")
            for i, server in enumerate(self.list_sql_servers, start=1):
                print(f"{i}. {server['name']}")
            selected_index: int = int(input("Enter the number of your choice: ")) - 1
            if 0 <= selected_index < len(self.list_sql_servers):
                selected_server = self.list_sql_servers[selected_index]
                self.server_name = selected_server['name']
                resource_group = extract_segment(selected_server['id'], 4)
                return selected_server['name'], resource_group
            else:
                print("Invalid selection.")
                return None, None

        else:
            print("Invalid choice. Please enter 1 or 2.")
            return None

    # FETCH PUBLIC IP ADDRESS
    # Retrieves the public IPv4 address
    # ///////////////////////////////////////////////////////////////
    def get_public_ipv4(self) -> Optional[str]:
        url = "https://api.ipify.org?format=json"
        
        response = make_api_request(
            url=url,
            method="GET"
        )
        
        if response and "ip" in response:
            self.ip_address = response["ip"]
            return self.ip_address
        else:
            print("Failed to fetch public IP.")
            return None

    # CREATE OR UPDATE FIREWALL RULE
    # Adds or updates the firewall rule for the selected SQL server
    # API Reference: https://learn.microsoft.com/en-us/rest/api/sql/firewall-rules/create-or-update?view=rest-sql-2021-11-01
    # ///////////////////////////////////////////////////////////////
    def create_or_update_firewall_rule(self) -> Optional[Dict[str, Any]]:
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

        url = (
            f"{self.base_url}/subscriptions/{self.subscription['subscriptionId']}/"
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

        response = make_api_request(
            url=url,
            method="PUT",
            headers=self.headers,
            json_data=body,
            create_role_assignment= self.subscription_manager.create_role_assignment,
            subscription = self.subscription
        )

        if response:
            print(f"Firewall rule '{firewall_rule_name}' created/updated successfully.")
            return response
        else:
            print(f"Failed to create/update firewall rule '{firewall_rule_name}'.")
            return None
        
    # UTILITY FUNCTIONS
    # ///////////////////////////////////////////////////////////////

    # CALCULATE IP RANGE
    # Generates the start and end of the IP range based on the provided IPv4
    # ///////////////////////////////////////////////////////////////
    def calculate_ip_range(self, ipv4: str) -> Tuple[Optional[str], Optional[str]]:
        if not ipv4:
            return None, None
        ip_parts = ipv4.split('.')
        start_ip = '.'.join(ip_parts[:3] + ['0'])
        end_ip = '.'.join(ip_parts[:3] + ['255'])
        return start_ip, end_ip
    
    # PROMPT FOR FIREWALL RULE NAME
    # Prompts the user to provide a firewall rule name or use the default
    # ///////////////////////////////////////////////////////////////
    def prompt_firewall_rule_name(self) -> str:
        user_input = input(f"\nEnter a new firewall rule name or press Enter to use '{self.firewall_name}': ").strip()
        return user_input if user_input else self.firewall_name

    # PROMPT FOR CUSTOM IP ADDRESS
    # Prompts the user to provide a custom IP address or use the current public IP
    # ///////////////////////////////////////////////////////////////
    def prompt_ip_address(self) -> Optional[str]:
        user_input = input(f"\nEnter a custom IPv4 address or press Enter to use your current public IP ({self.ip_address}): ").strip()
        return user_input if user_input else self.ip_address