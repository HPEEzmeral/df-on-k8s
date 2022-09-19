try:
    import ConfigParser as cp  # Python 2
except ImportError:
    import configparser as cp  # Python 3
try:
    from StringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3


class Parser(object):
    @staticmethod
    def get_properties_parser(file_name):
        file_p = open(file_name, 'r')
        try:
            # Need to add a fake section to the file so the config parser works, sadly a section is mandatory.
            file_str = '[root]\n' + file_p.read()
            ini_fp = StringIO(file_str)
        finally:
            file_p.close()

        parser = cp.SafeConfigParser()
        parser.readfp(ini_fp)

        return parser
