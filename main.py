# IMPORT MODULES
# ///////////////////////////////////////////////////////////////
from modules import *

# MAIN FUNCTION
# ///////////////////////////////////////////////////////////////
def main():

    auth_manager = AuthenticationManager()
    token, user_name = auth_manager.get_token()

    config_manager = ConfigManager()

    print(f"\nWelcome {user_name} to {config_manager.configurations['app_name']} {config_manager.configurations['version']}")

    while True:
        subscription_manager = SubscriptionManager(token, config_manager)
        selected_subscription = subscription_manager.select_subscription()

        print("\nWhat would you like to do?")
        options = ["Create appsettings", "Add/Update IPv4 to firewall"]
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        action = input("Enter the number of your choice: ").strip()

        if action == "1":
            settings_manager = AppSettingsManager(selected_subscription, token, subscription_manager, config_manager)
            settings_manager.fetch_and_save()
        elif action == "2":
            sql_manager = SQLFirewallRuleManager(selected_subscription, token, user_name, subscription_manager, config_manager)
            sql_manager.create_or_update_firewall_rule()
        else:
            print("Invalid option. Please enter a valid number.")
        
        another = input("\nDo you want to perform another action for a different service? (y/n): ").strip().lower()
        if another != 'y':
            print("Exiting the tool.")
            break

if __name__ == "__main__":
    main()