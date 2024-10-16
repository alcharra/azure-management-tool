import requests
import json
import os
from collections import defaultdict

class AppSettingsManager:
    
    def __init__(self, subscription_id, token, resource_groups):
        self.subscription_id = subscription_id
        self.resource_groups = [rg.lower() for rg in resource_groups]
        self.base_url = "https://management.azure.com"
        self.api_version = "2023-12-01"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def request(self, url):
        response = requests.post(url, headers=self.headers, json={})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
        
    def nest_dict(self, flat_dict):
        nested = defaultdict(dict)
        for key, value in flat_dict.items():
            parts = key.split("__")
            current = nested
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        return dict(nested)
    
    def save(self, data, output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Settings saved to {output_file}")

    def extract_resource_group(self, web_app_id):
        return web_app_id.split("/")[4]  # Resource group is the 5th element in the id path
    
    def list_web_apps(self):
        # https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/list?view=rest-appservice-2023-12-01
        url = (
            f"{self.base_url}/subscriptions/{self.subscription_id}/"
            f"providers/Microsoft.Web/sites?api-version={self.api_version}"
        )
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                web_apps = response.json().get("value", [])
                if not web_apps:
                    print("No web apps found in the subscription.")
                    return []
                for app in web_apps:
                    app['resourceGroup'] = self.extract_resource_group(app['id']).lower()
                if not self.resource_groups or all(rg not in [app['resourceGroup'] for app in web_apps] for rg in self.resource_groups):
                    print("No matching resource groups or no resource groups provided. Displaying all web apps.")
                    return web_apps
                filtered_web_apps = [
                    app for app in web_apps if app['resourceGroup'] in self.resource_groups
                ]
                return filtered_web_apps
            else:
                print(f"Failed to list web apps. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Error occurred while listing web apps: {e}")
            return []
        
    def select_web_apps(self):
        all_web_apps = self.list_web_apps()
        if not all_web_apps:
            print("No web apps found.")
            return None, None

        sorted_web_apps = sorted(all_web_apps, key=lambda x: x['name'])
        print("\nPlease select a web app:")
        for i, app in enumerate(sorted_web_apps, start=1):
            print(f"{i}. {app['name']} (Resource Group: {app['resourceGroup']})")
        selected_option = int(input("Enter the number of your choice: ")) - 1
        selected_app = sorted_web_apps[selected_option]
        selected_resource_group = selected_app['resourceGroup']
        return selected_app['name'], selected_resource_group
    
    def fetch_and_save(self):
        selected_webapp, selected_resourceGroup = self.select_web_apps()
        if not selected_webapp or not selected_resourceGroup:
            print("No web app selected. Aborting.")
            return
        # https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/list-application-settings?view=rest-appservice-2023-12-01
        settings_url = (
            f"{self.base_url}/subscriptions/{self.subscription_id}/"
            f"resourceGroups/{selected_resourceGroup}/"
            f"providers/Microsoft.Web/sites/{selected_webapp}/config/appsettings/list"
            f"?api-version={self.api_version}"
        )
        # https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/list-connection-strings?view=rest-appservice-2023-12-01
        conn_strings_url = (
            f"{self.base_url}/subscriptions/{self.subscription_id}/"
            f"resourceGroups/{selected_resourceGroup}/"
            f"providers/Microsoft.Web/sites/{selected_webapp}/config/connectionstrings/list"
            f"?api-version={self.api_version}"
        )

        appsettings_response = self.request(settings_url)
        appsettings = self.nest_dict(appsettings_response.get("properties", {}))
        conn_strings_response = self.request(conn_strings_url)
        conn_strings = {key: value['value'] for key, value in conn_strings_response.get("properties", {}).items()}

        combined = appsettings
        combined['ConnectionStrings'] = conn_strings

        self.save(combined, f"results/{selected_webapp}_appsettings.json")