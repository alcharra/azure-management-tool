import json

class ConfigManager:

    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.configurations = self.load_config()

    def load_config(self):
        with open(self.config_file_path, 'r') as file:
            return json.load(file)
        
    def select_env(self):
        print("\nPlease select an environment:")
        sorted_keys = sorted(self.configurations.keys())
        for i, key in enumerate(sorted_keys, start=1):
            print(f"{i}. {key}")
        selected_option = int(input("Enter the number of your choice: ")) - 1
        selected_key = sorted_keys[selected_option]
        return self.configurations[selected_key]
    
    def get_subscriptions(self):
        subscriptions = set()
        for env_name, env_data in self.configurations.items():
            for subscription_name in env_data:
                subscriptions.add(subscription_name)
        return list(subscriptions)