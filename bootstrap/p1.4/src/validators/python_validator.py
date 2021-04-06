import sys

from common.mapr_logger.log import Log
from common.version import Version
from validators.validator import Validator


class PythonValidator(Validator):
    PYTHON2_MIN = Version.parse("2.7.5")
    PYTHON2_MAX = Version.parse("2.7.99")
    PYTHON3_ERROR_MAX = Version.parse("3.2.99")
    PYTHON3_MIN = Version.parse("3.7.0")
    PYTHON3_MAX = Version.parse("3.8.99")

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

    def __init__(self):
        super(PythonValidator, self).__init__("python")
        PythonValidator._instance = self

        self.results[Validator.FOUND] = False
        self.results[Validator.VERSION] = "Unknown"

    def collect(self):
        Log.debug("Getting Python information...")

        python_major, python_version = self._get_python_version()
        Log.info("Python version: {0}".format(python_version))

        self.results[Validator.FOUND] = True
        self.results[Validator.VERSION] = python_version

        if python_major == 2:
            pmin = PythonValidator.PYTHON2_MIN
            pmax = PythonValidator.PYTHON2_MAX
        elif python_major == 3:
            pmin = PythonValidator.PYTHON3_MIN
            pmax = PythonValidator.PYTHON3_MAX

            if python_version <= PythonValidator.PYTHON3_ERROR_MAX:
                Log.error("The virtual environments created with your python version {0} are incompatible. "
                          "Please use Python 3.3 or greater".format(python_version))
                self.operation = Validator.OPERATION_INSTALL
                return
        else:
            Log.error("The major Python version '{0}' is not supported; Only version 2 and 3 supported".format(python_major))
            self.operation = Validator.OPERATION_TOO_NEW
            return

        expected = "Expected versions between {0} and {1} or between {2} and {3}"\
            .format(PythonValidator.PYTHON2_MIN, PythonValidator.PYTHON2_MAX,
                    PythonValidator.PYTHON3_MIN, PythonValidator.PYTHON3_MAX)

        if python_version > pmax or python_version < pmin:
            Log.warning("The Python version on this system is {0}. {1}"
                      .format(python_version, expected))
            self.operation = Validator.OPERATION_WARNING
        else:
            Log.debug("The Python version on this system is compatible")
            self.operation = Validator.OPERATION_OK

    @staticmethod
    def _get_python_version():
        return sys.version_info[0], Version(sys.version_info[0], sys.version_info[1], sys.version_info[2])
