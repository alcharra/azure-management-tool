# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
import json
import os
import math
from typing import Dict, Any, List, Optional, Callable, Tuple

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

# SEARCH AND SELECT FROM LIST
# Provides the user with an option to search or pick an item (Web App, SQL Server, etc.) from a list.
# Displays the list first and allows the user to either pick by number or refine the search.
# ///////////////////////////////////////////////////////////////
def search_and_select_from_list(
    items: List[Dict[str, Any]],
    item_key: str,
    item_type: str,
    select_message: str,
    extract_func: Optional[callable] = None,
    num_columns: int = 2,
    display_columns: bool = True
) -> Optional[Tuple[str, str]]:
    
    if not items:
        print(f"No {item_type} found.")
        return None

    def display_items(item_list: List[Dict[str, Any]]):
        if display_columns:
            display_items_in_columns([item[item_key] for item in item_list], num_columns)
        else:
            for i, item in enumerate(item_list, start=1):
                print(f"{i}. {item[item_key]}")

    def get_user_choice(matching_items: List[Dict[str, Any]]) -> Optional[Tuple[str, str]]:
        while len(matching_items) > 1:
            print(f"\nFound {len(matching_items)} matching {item_type.lower()}s.")
            display_items(matching_items)

            user_input = input(f"\nEnter more characters to refine search or the number of your choice: ").strip()

            if user_input.isdigit():
                selected_index = int(user_input) - 1
                if 0 <= selected_index < len(matching_items):
                    selected_item = matching_items[selected_index]
                    resource_group = extract_func(selected_item) if extract_func else None
                    return selected_item[item_key], resource_group
                else:
                    print("Invalid selection. Please enter a valid number.")
            else:
                matching_items = [item for item in items if user_input.lower() in item[item_key].lower()]

        if len(matching_items) == 1:
            selected_item = matching_items[0]
            resource_group = extract_func(selected_item) if extract_func else None
            return selected_item[item_key], resource_group
        else:
            print(f"No matching {item_type.lower()}s found.")
            return None

    print(select_message)
    display_items(items)

    while True:
        refine_choice = input(f"\nEnter a number to pick, or characters to refine the search: ").strip()

        if refine_choice.isdigit():
            selected_index = int(refine_choice) - 1
            if 0 <= selected_index < len(items):
                selected_item = items[selected_index]
                resource_group = extract_func(selected_item) if extract_func else None
                return selected_item[item_key], resource_group
            else:
                print("Invalid selection. Please enter a valid number.")
        else:
            matching_items = [item for item in items if refine_choice.lower() in item[item_key].lower()]
            return get_user_choice(matching_items)


# DISPLAY ITEMS IN COLUMNS (LONGEST ON RIGHT)
# Prints a list of items side by side in columns, with the longest items on the right
# ///////////////////////////////////////////////////////////////
def display_items_in_columns(items: List[str], num_columns: int = 2) -> None:
    total_items = len(items)
    num_rows = math.ceil(total_items / num_columns)

    max_item_length = max(len(item) for item in items)
    max_index_length = len(str(total_items))

    for row in range(num_rows):
        row_items = []
        for col in range(num_columns):
            index = row + col * num_rows
            if index < total_items:
                row_items.append(f"{str(index + 1).rjust(max_index_length)}. {items[index]:<{max_item_length + 5}}")
        print(" | ".join(row_items))

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