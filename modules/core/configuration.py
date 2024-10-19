# IMPORT STANDARD LIBRARY MODULES
# ///////////////////////////////////////////////////////////////
import json
from typing import Dict, Any

# CONFIGURATION MANAGER CLASS
# ///////////////////////////////////////////////////////////////
class ConfigManager:

    # INITIALISE CONFIG MANAGER
    # ///////////////////////////////////////////////////////////////
    def __init__(self) -> None:
        self.config_file_path: str = "config.json"
        self.configurations: Dict[str, Any] = self.load_config()

    # LOAD CONFIGURATIONS FROM FILE
    # ///////////////////////////////////////////////////////////////
    def load_config(self) -> Dict[str, Any]:
        with open(self.config_file_path, 'r') as file:
            return json.load(file)