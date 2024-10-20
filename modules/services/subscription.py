# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
import uuid
from typing import List, Dict, Optional, Any

# IMPORT UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////
from modules.utils import *

# SUBSCRIPTION MANAGER CLASS
# ///////////////////////////////////////////////////////////////
class SubscriptionManager:

    # INITIALISE SUBSCRIPTION MANAGER
    # ///////////////////////////////////////////////////////////////
    def __init__(self, token: str, config_manager: Any) -> None:
        self.config_manager = config_manager
        self.base_url: str = "https://management.azure.com"
        self.api_version: str = "2020-10-01"
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.role_eligibilities: Optional[List[Dict[str, Any]]] = self.list_role_eligibilities()

    # LIST ROLE ELIGIBILITIES
    # Retrieves the list of role eligibilities for the current subscription
    # API Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-eligibility-schedule-instances/get?view=rest-authorization-2020-10-01
    # ///////////////////////////////////////////////////////////////
    def list_role_eligibilities(self) -> Optional[List[Dict[str, Any]]]:
        url: str = (
            f"{self.base_url}/providers/Microsoft.Authorization/"
            f"roleEligibilityScheduleInstances?api-version={self.api_version}&$filter=asTarget()"
        )

        response: Optional[Dict[str, Any]] = make_api_request(
            url=url,
            method="GET",
            headers=self.headers
        )

        if response:
            return response.get("value", [])
        else:
            print("Failed to list role eligibilities.")
            return None

    # CREATE ROLE ASSIGNMENT
    # Creates a role assignment for the selected subscription
    # API Reference: https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/create?view=rest-authorization-2020-10-01
    # ///////////////////////////////////////////////////////////////
    def create_role_assignment(self, subscription_id: str, role_definition_id: str, principal_id: str) -> Optional[Dict[str, Any]]:
        url: str = (
            f"{self.base_url}/subscriptions/{subscription_id}/"
            f"providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{uuid.uuid4()}?"
            f"api-version={self.api_version}"
        )
        body: Dict[str, Any] = {
            "properties": {
                "roleDefinitionId": role_definition_id,
                "principalId": principal_id,
                "scope": f"/subscriptions/{subscription_id}",
                "Justification": f"Python tool: Requested access to role - {self.config_manager.configurations['app_name']}.",
                "scheduleInfo": {
                    "startDateTime": None,
                    "expiration": {
                        "type": "AfterDuration",
                        "duration": f"{self.config_manager.configurations['role_options']['role_assignment_duration']}"
                    }
                },
                "requestType": "SelfActivate",
                "ticketInfo": None
            }
        }

        response = make_api_request(
            url=url,
            method="PUT",
            headers=self.headers,
            json_data=body
        )

        if response:
            print(f"Role assignment schedule request created successfully.")
            return response
        else:
            print("Failed to create role assignment.")
            return None

    # SELECT SUBSCRIPTION
    # Prompts the user to select a subscription from the list of eligible roles
    # ///////////////////////////////////////////////////////////////
    def select_subscription(self) -> Dict[str, str]:
        if not self.role_eligibilities:
            print("No eligible roles found.")
            raise Exception("No eligible roles found.")

        print("\nPlease select a subscription:")
        for i, role in enumerate(self.role_eligibilities, start=1):
            subscription_name = role['properties']['expandedProperties']['scope'].get('displayName', 'Unknown')
            subscription_id = extract_segment(role['properties']['expandedProperties']['scope'].get('id'), 2)
            print(f"{i}. {subscription_name} (Subscription ID: {subscription_id})")

        selected_index: int = int(input("Enter the number of your choice: ")) - 1
        selected_role = self.role_eligibilities[selected_index]

        selected_subscription_id = extract_segment(selected_role['properties']['expandedProperties']['scope'].get('id'), 2)
        principal_id = selected_role['properties']['expandedProperties']['principal'].get('id')
        role_definition_id = selected_role['properties']['expandedProperties']['roleDefinition'].get('id')

        return {
            "subscriptionId": selected_subscription_id,
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id
        }