import requests
import json
import uuid

class SubscriptionManager:

    def __init__(self, token, subscriptions):
        self.base_url = "https://management.azure.com"
        self.api_version = "2020-10-01"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.subscriptions = subscriptions

    def list_role_eligibilities(self):
        # https://learn.microsoft.com/en-us/rest/api/authorization/role-eligibility-schedule-instances/get?view=rest-authorization-2020-10-01
        url = (
            f"{self.base_url}/providers/Microsoft.Authorization/"
            f"roleEligibilityScheduleInstances?api-version={self.api_version}&$filter=asTarget()"
        )
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()["value"]
            else:
                print(f"Failed to list role eligibilities. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error occurred while listing role eligibilities: {e}")
            return None
        
    def list_active_role_assignments(self):
        # https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-instances/get?view=rest-authorization-2020-10-01
        url = (
            f"{self.base_url}/providers/Microsoft.Authorization/"
            f"roleAssignmentScheduleInstances?api-version={self.api_version}&$filter=asTarget()"
        )
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()["value"]
            else:
                print(f"Failed to list active role assignments. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error occurred while listing active role assignments: {e}")
            return None
        
    def extract_subscription_guid(self, subscription_id):
        return subscription_id.split("/")[2] if len(subscription_id.split("/")) > 2 else subscription_id
    
    def find_matching_subscriptions(self, role_eligibilities):
        matching_roles = []
        for eligibility in role_eligibilities:
            properties = eligibility.get("properties", {})
            expanded_properties = properties.get("expandedProperties", {})
            scope = expanded_properties.get("scope", {})
            subscription_name = scope.get("displayName")
            if subscription_name in self.subscriptions:
                matching_roles.append({
                    "subscriptionId": self.extract_subscription_guid(scope.get("id", "")),
                    "subscriptionName": subscription_name,
                    "roleDefinitionId": expanded_properties.get("roleDefinition", {}).get("id"),
                    "principalId": expanded_properties.get("principal", {}).get("id")
                })
        return matching_roles
            
    def check_and_create_role_assignments(self, matching_roles, active_assignments):
        for role in matching_roles:
            subscription_id = role['subscriptionId']
            role_definition_id = role['roleDefinitionId']
            principal_id = role['principalId']
            is_active = False
            for assignment in active_assignments:
                scope = assignment.get('properties', {}).get('scope', "")
                if scope:
                    assignment_subscription_id = scope.split('/')[2] if len(scope.split('/')) > 2 else None
                    if assignment_subscription_id == subscription_id:
                        is_active = True
                        break
            if not is_active:
                print(f"Creating new role assignment for subscription: {subscription_id}")
                self.create_role_assignment(subscription_id, role_definition_id, principal_id)

    def create_role_assignment(self, subscription_id, role_definition_id, principal_id):
        # https://learn.microsoft.com/en-us/rest/api/authorization/role-assignment-schedule-requests/create?view=rest-authorization-2020-10-01
        url = (
            f"{self.base_url}/subscriptions/{subscription_id}/"
            f"providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{uuid.uuid4()}?"
            f"api-version={self.api_version}"
        )
        body = {
            "properties": {
                "roleDefinitionId": role_definition_id,
                "principalId": principal_id,
                "scope": f"/subscriptions/{subscription_id}",
                "Justification": "Python tool: Requested access to role.",
                "scheduleInfo": {
                    "startDateTime": None,
                    "expiration": {
                        "type": "AfterDuration",
                        "duration": "PT30M"
                    }
                },
                "requestType": "SelfActivate",
                "ticketInfo": None
            }
        }
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(body))
            if response.status_code in (200, 201):
                print(f"Role assignment schedule request created successfully.")
                return response.json()
            else:
                print(f"Failed to create role assignment. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error occurred while creating role assignment: {e}")
            return None
        
    def select_subscription(self, matching_roles):
        if len(matching_roles) > 1:
            print("\nPlease select a subscription:")
            for i, role in enumerate(matching_roles, start=1):
                print(f"{i}. {role['subscriptionName']} (Subscription ID: {role['subscriptionId']})")
            selected_index = int(input("Enter the number of your choice: ")) - 1
            selected_role = matching_roles[selected_index]
            return selected_role['subscriptionId'], selected_role['subscriptionName']
        else:
            return matching_roles[0]['subscriptionId'], matching_roles[0]['subscriptionName']
        
    def initiate_subscription(self):
        role_eligibilities = self.list_role_eligibilities()
        if not role_eligibilities:
            print("No eligible roles found.")
            return None, None

        matching_roles = self.find_matching_subscriptions(role_eligibilities)
        if not matching_roles:
            print("No matching roles found for the provided subscriptions.")
            return None, None

        active_assignments = self.list_active_role_assignments()

        self.check_and_create_role_assignments(matching_roles, active_assignments)

        return self.select_subscription(matching_roles)