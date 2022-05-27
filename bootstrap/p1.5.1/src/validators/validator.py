from common.mapr_exceptions.ex import NotFoundException


class Validator(object):
    FOUND = 'found'
    ERROR = 'error'
    VERSION = 'version'

    OPERATION_NONE = 0
    OPERATION_OK = 1
    OPERATION_UPGRADE = 2
    OPERATION_TOO_NEW = 3
    OPERATION_INSTALL = 4
    OPERATION_WARNING = 5

    __checkers_list__ = []

    def __init__(self, name, package_name=None):
        # The results of the scan of the user's system
        self.results = {}
        # The operation to be taken on the system
        self.operation = Validator.OPERATION_NONE
        # The version of this particular software package that will be installed
        self.install_version = 0.0
        # The installation file
        self.install_file = None
        # Any post installation steps you want to show the user to do after the installation is complete
        self.post_install_manual_steps = []
        # The name of the package. Used to query and remove the package using rpm
        self.package_name = package_name
        # The name of the checker
        self.name = name

        Validator.__checkers_list__.append(self)

    @staticmethod
    def get_checker(validator_type):
        for validator in Validator.__checkers_list__:
            if isinstance(validator, validator_type):
                return validator

        raise NotFoundException('A validator of type %s is not registered.' % str(validator_type))

    @staticmethod
    def get_checkers_list():
        return Validator.__checkers_list__

    def get(self, key):
        return self.results.get(key)
