from common.mapr_logger.log import Log
from common.os_command import OSCommand
from validators.validator import Validator


class OpenshiftClientValidator(Validator):
    _instance = None

    @staticmethod
    def get_result(key):
        if OpenshiftClientValidator._instance is None:
            return None
        return OpenshiftClientValidator._instance.results.get(key)

    @staticmethod
    def get_operation():
        if OpenshiftClientValidator._instance is None:
            return None
        return OpenshiftClientValidator._instance.operation

    def __init__(self):
        super(OpenshiftClientValidator, self).__init__('oc')

    def collect(self):
        Log.debug('Checking for oc (OpenShift CLI) installation...')
        response, status = OSCommand.run2("command -v oc")
        if status == 0:
            Log.info("Looking good... Found oc (OpenShift CLI) installed", True)
            self.operation = Validator.OPERATION_OK
        else:
            self.operation = Validator.OPERATION_NONE
            Log.error("You will need to have oc (OpenShift CLI) installed on this machine.")
            Log.error("To install oc please see: https://docs.openshift.com/container-platform/3.11/cli_reference/get_started_cli.html")
