import os
import tempfile

class FileUtils(object):
    """
    Find an occurrence of a yaml key in a file and replace the value for that key.
    filename - the yaml file to load the contents of to check for replacements
    replace_dict - keys/values of where the key is also the key in the yaml file and value is the replacement

    return the new file name and if the file has changed or is the original file
    """
    @staticmethod
    def replace_yaml_value(filename, replace_dict):
        change = False
        with open(filename, 'r') as file:
            data = file.read()
        for key, val in replace_dict.items():
            if (str(data).find(key)) >= 0:
                change = True
                if isinstance(val, bytes):
                    data = data.replace(key, val.decode('utf-8'))
                else:
                    data = data.replace(key, val)
        if change:
            fd, path = tempfile.mkstemp(suffix=".yaml", prefix="mapr_", text=True)
            with open(path, 'w') as f:
                f.write(data)
            os.close(fd)
            yaml_file = path
        else:
            yaml_file = filename
        return yaml_file, change
