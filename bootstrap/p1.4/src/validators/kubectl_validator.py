import os
import re

from common.mapr_logger.log import Log
from common.os_command import OSCommand
from common.version import Version
from validators.validator import Validator


class KubectlValidator(Validator):
    _instance = None

    @staticmethod
    def get_result(key):
        if KubectlValidator._instance is None:
            return None
        return KubectlValidator._instance.results.get(key)

    @staticmethod
    def get_operation():
        if KubectlValidator._instance is None:
            return None
        return KubectlValidator._instance.operation

    def __init__(self):
        super(KubectlValidator, self).__init__('kubectl')
        self.client_version = None
        self.server_version = None

    def collect(self):
        Log.debug('Checking kubectl is installed correctly...')
        response, status = OSCommand.run2("command -v kubectl")
        if status != 0:
            self.operation = Validator.OPERATION_INSTALL
            Log.error("You will need to have kubectl installed on this machine.")
            Log.error("To install kubectl please see: https://kubernetes.io/docs/tasks/tools/install-kubectl/")
            return
        Log.info("Looking good... Found kubectl. Checking client and server versions...")

        self.operation = Validator.OPERATION_WARNING
        print("")
        Log.info("Checking kubectl version(s)...", stdout=True)
        response, status = OSCommand.run2("kubectl version --short")
        if status != 0:
            Log.warning("Could not determine kubectl versions; {0}".format(response))
            return

        versions = response.strip(os.linesep).split(os.linesep)
        if len(versions) != 2:
            Log.warning("Unexpected version response: {0}".format(versions))
            return

        match = re.search(": v(\\d+.\\d+.\\d+)", versions[0])
        if match is None or len(match.groups()) != 1:
            Log.warning("Could not parse client version from version string: {0}".format(versions[0]))
            return
        client_version = match.group(1)
        self.client_version = Version.parse(client_version)
        Log.info("Kubectl client version is: {0}".format(client_version))

        match = re.search(": v(\\d+.\\d+.\\d+)", versions[1])
        if match is None or len(match.groups()) != 1:
            Log.warning("Could not parse server version from version string: {0}".format(versions[1]))
            return
        server_version = match.group(1)
        self.server_version = Version.parse(server_version)
        Log.info("Kubectl server version is: {0}".format(server_version))

        # Now that we have client and server versions, we need to do some sort of comparison
        # They don't need to match but should be relatively close in versions to each other
        if self.client_version != self.server_version:
            if self.client_version.major != self.server_version.major:
                Log.error("The kubectl client and server versions are drastically different; Bootstrapping might not "
                          "work correctly Client: {0}, Server: {1}".format(self.client_version, self.server_version))
                return

            minor_diff = abs(self.client_version.minor - self.server_version.minor)
            # Here is where we make the decision to warn the user to proceed or not
            if minor_diff > 2:
                Log.warning("The kubectl client and server minor versions are not close to each other; Bootstrapping might not "
                            "work correctly Client: {0}, Server: {1}".format(self.client_version, self.server_version))
                return

        self.operation = Validator.OPERATION_OK
