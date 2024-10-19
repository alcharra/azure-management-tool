# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
import json
import os
from typing import Dict, Any, Optional, Callable

# IMPORT THIRD-PARTY PACKAGES
# ///////////////////////////////////////////////////////////////
import requests

# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////

# MAKE API REQUEST
# Sends an HTTP request (GET, POST or PUT) and handles the response with error handling and retries
# ///////////////////////////////////////////////////////////////
def make_api_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    retry_callback: Optional[Callable] = None,
    create_role_assignment: Optional[Callable] = None,
    subscription: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        else:
            raise ValueError("Invalid HTTP method. Only 'GET', 'POST' and 'PUT' are supported.")

        if response.status_code in (200, 201):
            return response.json()

        elif response.status_code == 403:
            error_data = response.json().get("error", {})
            if error_data.get("code") == "AuthorizationFailed":
                print(f"Authorisation failed: {error_data.get('message')}")
                
                if subscription and create_role_assignment:
                    print("Creating a new role assignment to grant necessary permissions...")
                    create_role_assignment(subscription['subscriptionId'], subscription['roleDefinitionId'], subscription['principalId'])

                if retry_callback:
                    print("Retrying the operation after successful role assignment...")
                    return retry_callback()
            else:
                print(f"Failed request. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        else:
            print(f"Failed request. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"Error occurred while making the API request: {e}")
        return None

# SAVE DATA TO JSON FILE
# Saves the provided data as a JSON file with error handling
# ///////////////////////////////////////////////////////////////
def save_to_json(data: Dict[str, Any], output_file: str) -> None:
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {output_file}")
    except OSError as e:
        print(f"Failed to save file: {e}")
        return None
    except TypeError as e:
        print(f"Failed to serialize data to JSON: {e}")
        return None
    
# EXTRACT PART OF A STRING BASED ON INDEX
# Safely extracts a specific part of a string using a given index
# ///////////////////////////////////////////////////////////////
def extract_segment(string: str, index: int) -> str:
    try:
        return string.split("/")[index]
    except IndexError:
        return ""