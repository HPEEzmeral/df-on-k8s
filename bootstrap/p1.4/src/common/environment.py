import os

try:
    import ConfigParser as cp  # Python 2
except ImportError:
    import configparser as cp  # Python 3
try:
    from StringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3


class Environment(object):
    def __init__(self, args):
        self.env_parser = None
        self.env_override_parser = None

        #  TODO: SWF: use arg parser to trigger environment from command line or this might go away entirely
        # if len(args) != 1 and len(args) != 3:
        #     raise Exception("System arguments must be 0 (environment) or 2 (locally)")
        #
        # if len(sys.argv) == 3:
        #     if not os.path.exists(sys.argv[1]):
        #         raise Exception("{0} environment file does not exist".format(sys.argv[1]))
        #     if not os.path.exists(sys.argv[2]):
        #         raise Exception("{0} override environment file does not exist".format(sys.argv[2]))
        #
        #     with open(sys.argv[1], 'r') as f:
        #         config_string = '[root] \n' + f.read()
        #     ini_fp = StringIO.StringIO(config_string)
        #     self.env_parser = ConfigParser.ConfigParser()
        #     self.env_parser.readfp(ini_fp)
        #
        #     with open(sys.argv[2], 'r') as f:
        #         config_string = '[root] \n' + f.read()
        #     ini_fp = StringIO.StringIO(config_string)
        #     self.env_override_parser = ConfigParser.ConfigParser()
        #     self.env_override_parser.readfp(ini_fp)

    def get(self, name, default=None):
        if not name:
            raise Exception("name must be supplied")

        if self.env_parser is None:
            result = os.environ.get(name)
            return result

        try:
            return self.env_override_parser.get("root", name)
        except cp.NoOptionError:
            try:
                return self.env_parser.get("root", name)
            except cp.NoOptionError as noe:
                if default is not None:
                    return default

                raise noe

    def get_int(self, name, default=None):
        return int(self.get(name, default))
