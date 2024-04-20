import json
from os import mkdir as os_mkdir
from os.path import isfile as os_isfile, isdir as os_isdir, join as os_pathjoin

class Storage(object):
    """
        Read and write bot configuration to JSON file for permanent storage.
        This class is intended to be replaced by a Database implementation as the saved data grows.
    """
    
    def __init__(self, dir_data, file_system, file_guild):
        self.file_system = os_pathjoin(dir_data, f"{file_system}.json")
        self.file_guild = os_pathjoin(dir_data, f"{file_guild}.json")
        if not os_isdir(dir_data):
            os_mkdir(dir_data)
        if not os_isfile(self.file_system):
            f = open(self.file_system, 'w')
            f.close
        if not os_isfile(self.file_guild):
            f = open(self.file_guild, 'w')
            f.close
    
    def load_system_guild(self):
        with open(self.file_system, 'r') as file_system:
            system_guild = json.load(file_system)
        return system_guild
    
    def save_system_guild(self, system_guild):
        with open(self.file_system, 'w') as file_system:
            json.dump(system_guild, file_system, indent = 4)
    
    def load_registered_guild(self):
        with open(self.file_guild, 'r') as file_guild:
            registered_guild = json.load(file_guild)
        return registered_guild
    
    def save_registered_guild(self, registered_guild):
        with open(self.file_guild, 'w') as file_guild:
            json.dump(registered_guild, file_guild, indent = 4)
