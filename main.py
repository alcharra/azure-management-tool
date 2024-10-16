from module.configuration import ConfigManager
from module.authentication import AuthenticationManager
from module.services.appsettings import AppSettingsManager
from module.services.firewall import SQLFirewallRuleManager
from module.services.subscription import SubscriptionManager

def main():

    auth_manager = AuthenticationManager()
    token = auth_manager.get_token()
    config_manager = ConfigManager('config.json')

    while True:
        subscription_manager = SubscriptionManager(token, config_manager.get_subscriptions())
        subscriptionId, subscriptionName = subscription_manager.initiate_subscription()
        
        print("\nWhat would you like to do?")
        options = ["Create appsettings", "Add/Update IPv4 to firewall"]
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        action = input("Enter the number of your choice: ").strip()

        selected_env = config_manager.select_env()
        resource_groups = selected_env[f"{subscriptionName}"]["resourceGroupName"]

        if action == "1":
            settings_manager = AppSettingsManager(subscriptionId, token, resource_groups)
            settings_manager.fetch_and_save()
        elif action == "2":
            sql_manager = SQLFirewallRuleManager(subscriptionId, token, auth_manager.get_user_name_from_token(), resource_groups)
            sql_manager.create_or_update_firewall_rule()
        else:
            print("Invalid option. Please enter a valid number.")

        another = input("\nDo you want to perform another action for a different service? (y/n): ").strip().lower()
        if another != 'y':
            print("Exiting the tool.")
            break

if __name__ == "__main__":
    main()