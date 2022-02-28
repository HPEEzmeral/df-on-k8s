import sys

from common.mapr_logger.log import Log
from common.version import Version
from validators.validator import Validator


class PythonValidator(Validator):
    PYTHON3_MIN = Version.parse("3.6.0")
    PYTHON3_MAX = Version.parse("3.9.99")

    _instance = None

    @staticmethod
    def get_result(key):
        if PythonValidator._instance is None:
            return None
        return PythonValidator._instance.results.get(key)

    @staticmethod
    def get_operation():
        if PythonValidator._instance is None:
            return None
        return PythonValidator._instance.operation

    def __init__(self, no_python_check):
        super(PythonValidator, self).__init__("python")
        PythonValidator._instance = self

        self.no_python_check = no_python_check
        self.results[Validator.FOUND] = False
        self.results[Validator.VERSION] = "Unknown"

    def collect(self):
        Log.debug("Getting Python information...")

        python_major, python_version = self._get_python_version()
        Log.info("Python version: {0}".format(python_version))

        self.results[Validator.FOUND] = True
        self.results[Validator.VERSION] = python_version
        pmin = PythonValidator.PYTHON3_MIN
        pmax = PythonValidator.PYTHON3_MAX

        if python_major != 3:
            Log.error("The major Python version '{0}' is not supported; Only version 3 supported".format(python_major))

            if self.no_python_check:
                self.operation = Validator.OPERATION_WARNING
                return

            self.operation = Validator.OPERATION_TOO_NEW
            return

        if python_version > pmax or python_version < pmin:
            expected = "Expected versions between {0} and {1}".format(PythonValidator.PYTHON3_MIN, PythonValidator.PYTHON3_MAX)
            Log.warning("The Python version on this system is {0}. {1}".format(python_version, expected))
            self.operation = Validator.OPERATION_WARNING
        else:
            Log.debug("The Python version on this system is compatible")
            self.operation = Validator.OPERATION_OK

    @staticmethod
    def _get_python_version():
        return sys.version_info[0], Version(sys.version_info[0], sys.version_info[1], sys.version_info[2])
