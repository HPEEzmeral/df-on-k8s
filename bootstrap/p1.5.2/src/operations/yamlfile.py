class YamlFile:
    def __init__(self, file_id, file_name, file_path, type, is_upgradable=True, ignore_not_found=False):
        self.file_id = file_id
        self.file_name = file_name
        self.file_path = file_path
        self.type = type
        self.is_upgradable = is_upgradable
        self.ignore_not_found = ignore_not_found
