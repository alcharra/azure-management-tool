# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
from collections import defaultdict
from typing import List, Dict, Any, Optional

# IMPORT UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////
from modules.utils import *

# APP SETTINGS MANAGER CLASS
# ///////////////////////////////////////////////////////////////
class AppSettingsManager:
    
    # INITIALISE APP SETTINGS MANAGER
    # ///////////////////////////////////////////////////////////////
    def __init__(self, subscription: Dict[str, str], token: str, subscription_manager: Any, config_manager: Any) -> None:
        self.subscription_manager: Any = subscription_manager
        self.config_manager: Any = config_manager
        self.subscription: Dict[str, str] = subscription
        self.base_url: str = "https://management.azure.com"
        self.api_version: str = "2023-12-01"
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.list_web_apps: Optional[List[Dict[str, Any]]] = self.list_web_apps()

    # LIST ALL WEB APPS
    # Lists all web apps for the current subscription
    # API Reference: https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/list?view=rest-appservice-2023-12-01
    # ///////////////////////////////////////////////////////////////
    def list_web_apps(self) -> Optional[List[Dict[str, Any]]]:
        url: str = (
            f"{self.base_url}/subscriptions/{self.subscription['subscriptionId']}/"
            f"providers/Microsoft.Web/sites?api-version={self.api_version}"
        )

        response: Optional[Dict[str, Any]] =  make_api_request(
            url=url,
            method="GET",
            headers=self.headers,
            retry_callback=self.list_web_apps,
            create_role_assignment= self.subscription_manager.create_role_assignment,
            subscription = self.subscription
        )

        if isinstance(response, dict):
            web_apps: List[Dict[str, Any]] = response.get("value", [])
        elif isinstance(response, list):
            web_apps: List[Dict[str, Any]] = response
        else:
            print("Unexpected response format. Returning an empty list.")
            return []

        if not web_apps:
            print("No web apps found in the subscription.")
            return []

        for app in web_apps:
            app['resourceGroup'] = extract_segment(app['id'], 4).lower()

        return web_apps

    # FETCH APP SETTINGS AND SAVE TO FILE
    # Fetches app settings and connection strings for the selected web app
    # API Reference: https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/list-application-settings?view=rest-appservice-2023-12-01
    # ///////////////////////////////////////////////////////////////
    def fetch_and_save(self) -> None:
        selected_webapp, selected_resourceGroup = search_and_select_from_list(
            items = self.list_web_apps,
            item_key = 'name',
            item_type = 'Web App',
            select_message = "\nPlease select a web app from the list:",
            extract_func = lambda app: extract_segment(app['id'], 4),
            num_columns = self.config_manager.configurations['display_options']['number_of_columns'],
            display_columns = self.config_manager.configurations['display_options']['display_items_in_columns']
        )

        if not selected_webapp or not selected_resourceGroup:
            print("No web app selected. Aborting.")
            return

        settings_url: str = (
            f"{self.base_url}/subscriptions/{self.subscription['subscriptionId']}/"
            f"resourceGroups/{selected_resourceGroup}/"
            f"providers/Microsoft.Web/sites/{selected_webapp}/config/appsettings/list"
            f"?api-version={self.api_version}"
        )
        conn_strings_url: str = (
            f"{self.base_url}/subscriptions/{self.subscription['subscriptionId']}/"
            f"resourceGroups/{selected_resourceGroup}/"
            f"providers/Microsoft.Web/sites/{selected_webapp}/config/connectionstrings/list"
            f"?api-version={self.api_version}"
        )

        appsettings_response: Dict[str, Any] = make_api_request(
            url=settings_url,
            method="POST",
            headers=self.headers,
            json_data={},
            retry_callback=self.fetch_and_save,
            create_role_assignment= self.subscription_manager.create_role_assignment,
            subscription = self.subscription
        )
        conn_strings_response: Dict[str, Any] = make_api_request(
            url=conn_strings_url,
            method="POST",
            headers=self.headers,
            json_data={},
            retry_callback=self.fetch_and_save,
            create_role_assignment= self.subscription_manager.create_role_assignment,
            subscription = self.subscription
        )

        appsettings: Dict[str, Any] = self.nest_dict(appsettings_response.get("properties", {}))
        conn_strings: Dict[str, str] = {key: value['value'] for key, value in conn_strings_response.get("properties", {}).items()}

        combined: Dict[str, Any] = appsettings
        combined['ConnectionStrings'] = conn_strings

        save_to_json(combined, f"results/{selected_webapp}_appsettings.json")

    # UTILITY FUNCTIONS
    # ///////////////////////////////////////////////////////////////

    # NEST DICTIONARY DATA
    # Converts a flat dictionary to a nested dictionary
    # ///////////////////////////////////////////////////////////////
    def nest_dict(self, flat_dict: Dict[str, str]) -> Dict[str, Any]:
        nested: Dict[str, Any] = defaultdict(dict)
        for key, value in flat_dict.items():
            parts = key.split("__")
            current = nested
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        return dict(nested)
