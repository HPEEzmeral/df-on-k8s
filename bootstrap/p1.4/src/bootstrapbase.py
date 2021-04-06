import argparse
import os
import platform
import signal
import sys
from datetime import datetime

from common.const import Constants
from common.mapr_logger.log import Log
from common.os_command import OSCommand
from common.prompts import Prompts
from validators.kubectl_validator import KubectlValidator
from validators.python_validator import PythonValidator
from validators.validator import Validator

# TODO: This needs to be change with every public release. Hopefully we automate this in the future.
BOOTSTRAP_BUILD_VERSION_NO = "1.4.0.0 ECP53"


class BootstrapBase(object):
    INSTALL = "install"
    UNINSTALL = "uninstall"
    UPGRADE = "upgrade"
    NOW = datetime.now()
    _prompts = None

    def __init__(self, run_type):
        # If True, core and cloud prompts will be enabled
        self.core_install_enabled = True
        self.prompt_mode = Prompts.PROMPT_MODE_STR
        self.prompt_response_file = None
        self.parsed_args = None
        self.run_type = run_type
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_dir = os.path.abspath(os.path.join(self.base_dir, ".."))
        self.log_config_file = os.path.join(self.base_dir, Constants.LOGGER_CONF)

        signal.signal(signal.SIGINT, self.exit_application)

    def run(self):
        logdir = os.path.join(self.script_dir, "logs")
        if os.path.exists(logdir):
            if not os.path.isdir(logdir):
                print("ERROR: {0} is not a directory and cannot be used as a log directory".format(logdir))
                BootstrapBase.exit_application(1)
        else:
            os.mkdir(logdir)

        logname = os.path.join(logdir, BootstrapBase.NOW.strftime("bootstrap-%m-%d_%H:%M:%S_"))
        logname += self.run_type + ".log"
        Log.initialize(self.log_config_file, logname)

        BootstrapBase._prompts = Prompts.initialize(self.prompt_mode, self.prompt_response_file)
        Log.info("Prompt mode: {0}, response file: {1}".format(self.prompt_mode, self.prompt_response_file))

    def _parse_args(self):
        self.arg_parser = argparse.ArgumentParser(prog='bootstrap.sh ' + self.run_type)
        self.arg_parser.add_argument("-m", "--mode", action="store",
                                     default=self.prompt_mode,
                                     help="prompt mode ({0}, {1}, {2})".format(Prompts.PROMPT_MODE_STR,
                                                                               Prompts.HEADLESS_MODE_STR,
                                                                               Prompts.RECORD_MODE_STR))
        self.arg_parser.add_argument("-r", "--response-file", action="store",
                                     default=self.prompt_response_file, help="prompt response file")
        self.arg_parser.add_argument("--std_csimount", action="store_true", default=False, help="force /var/lib/mount volume for csi")
        self.arg_parser.add_argument("--ecp_csimount", action="store_true", default=False, help="force /var/lib/docker/mount volume for csi")

        if self.run_type == BootstrapBase.INSTALL:
            self.arg_parser.add_argument("--setup_only", action="store_true", default=False,
                                         help="Perform virtualenv install only")

        if self.run_type == BootstrapBase.INSTALL:
            self.arg_parser.add_argument("--drill_install", action="store_true", default=False, help=argparse.SUPPRESS)
            self.arg_parser.add_argument("--openshift_install", action="store_true", default=False,
                                         help=argparse.SUPPRESS)
            # Not intended for customer use. No guarantees given if these are set to True
            self.arg_parser.add_argument("--cloud_install", action="store_true", default=False, help=argparse.SUPPRESS)
            self.arg_parser.add_argument("--core_install", action="store_true", default=False, help=argparse.SUPPRESS)
        else:
            self.arg_parser.add_argument("--drill_uninstall", action="store_true", default=False,
                                         help=argparse.SUPPRESS)
            self.arg_parser.add_argument("--openshift_uninstall", action="store_true", default=False,
                                         help=argparse.SUPPRESS)
            self.arg_parser.add_argument("--core_uninstall", action="store_true", default=False, help=argparse.SUPPRESS)

        self.parsed_args = self.arg_parser.parse_args()
        self.prompt_mode = self.parsed_args.mode
        self.prompt_response_file = self.parsed_args.response_file

        try:
            self.prompt_mode, self.prompt_response_file = Prompts.validate_commandline_options(self.prompt_mode,
                                                                                           self.prompt_response_file)
        except Exception as e:
            self.arg_parser.print_help(sys.stderr)
            print("Error: "+str(e))
            sys.exit(1)

    def prologue(self):
        title = os.linesep + "Ezmeral Data Fabric for Kubernetes Bootstrap " + self.run_type.capitalize()
        title += " (Version {0})".format(BOOTSTRAP_BUILD_VERSION_NO)
        Log.info(title, True)
        Log.info("Copyright 2021 Hewlett Packard Enterprise (HPE), All Rights Reserved", True)
        Log.info("https://www.hpe.com/us/en/software/licensing.html", True)
        Log.info("Platform: {0}".format(platform.platform()))
        print("")

    def check_ready(self):
        print(os.linesep)
        Log.info("We are now ready to {0} your Kubernetes components...".format(
            self.run_type), True)
        ready = self._prompts.prompt_boolean("Continue with {0}?".format(self.run_type), True,
                                             key_name="CONTINUE_INSTALL")
        if not ready:
            Log.error("User not ready to {0} system components".format(self.run_type))
            return False
        return True

    @staticmethod
    def configure_kubernetes(cloud_instance=None):
        print(os.linesep)
        Log.info("Ensuring proper kubernetes configuration...", True)
        Log.info("Checking kubectl can connect to your kubernetes cluster...", True)
        response, status = OSCommand.run2("kubectl get nodes")
        if status != 0:
            Log.error("Cannot connect to Kubernetes. Make sure kubectl is pre-configured to communicate with a Kubernetes cluster.")
            BootstrapBase.exit_application(4)

        Log.info("Looking good... Connected to Kubernetes", True)
        res, status = OSCommand.run2("kubectl config current-context")
        res = res.strip("\n")
        Log.info("Current Kubernetes context: {0}".format(res), True)
        rows = response.splitlines()
        Log.info("Number of nodes present in the cluster: {0}".format(len(rows) - 1), True)
        column = rows[1].split()
        version = column[4]
        Log.info("Kubernetes version present on nodes: {0}".format(version), True)
        if cloud_instance is not None:
            cloud_instance.configure_cloud()

    @staticmethod
    def python_check():
        python_validator = PythonValidator()
        python_validator.collect()

        if python_validator.operation == Validator.OPERATION_INSTALL:
            BootstrapBase.exit_application(1)

        if python_validator.operation == Validator.OPERATION_WARNING:
            if not BootstrapBase._prompts.prompt_boolean("Continue with an incompatible Python version?", False,
                                                         key_name="PYTHON_INCOMPATIBLE_CONTINUE"):
                BootstrapBase.exit_application(1)
        elif python_validator.operation != Validator.OPERATION_OK:
            BootstrapBase.exit_application(1)

    @staticmethod
    def check_laptop_tools():
        kubectl_validator = KubectlValidator()
        kubectl_validator.collect()
        if kubectl_validator.operation == Validator.OPERATION_WARNING:
            if not BootstrapBase._prompts.prompt_boolean("Continue with potentially incompatible kubectl versions?",
                                                         False,
                                                         key_name="KUBECTL_INCOMPATIBLE_CONTINUE"):
                BootstrapBase.exit_application(1)
        elif kubectl_validator.operation != Validator.OPERATION_OK:
            BootstrapBase.exit_application(3)

    @staticmethod
    def complete_installation():
        print(os.linesep)

        msg = "This Kubernetes environment"
        warnings = Log.get_warning_count()
        errors = Log.get_error_count()

        if errors > 0 and warnings > 0:
            msg = "{0} had {1} error(s) and {2} warning(s) during the bootstrapping process for the Data Fabric" \
                .format(msg, errors, warnings)
            Log.error(msg)
        elif errors > 0 and warnings == 0:
            msg = "{0} had {1} error(s) during the bootstrapping process for the Data Fabric".format(msg, errors)
            Log.error(msg)
        elif errors == 0 and warnings > 0:
            msg = "{0} had {1} warnings(s) during the bootstrapping process for the Data Fabric".format(msg, warnings)
            Log.warning(msg)
        else:
            msg = "{0} has been successfully bootstrapped for the Data Fabric".format(msg)
            Log.info(msg, True)
            Log.info("Data Fabric components can now be created via the newly installed operators", True)

        if errors > 0 or warnings > 0:
            msg = "Please check the bootstrap log file for this session here: {0}".format(Log.get_log_filename())
            Log.warning(msg)
            msg = "Errors are often caused by insufficient permissions to alter the Kubernetes environment."
            Log.info(msg)

        Log.info("")

    @staticmethod
    def exit_application(signum, _=None):
        if signum == 0:
            Log.info("Bootstrap terminated {0}".format(signum))
        else:
            print(os.linesep)
            Log.warning("Bootstrap terminated {0}".format(signum))
        if BootstrapBase._prompts is not None:
            BootstrapBase._prompts.write_response_file()
            BootstrapBase._prompts = None
        Log.close()
        exit(signum)
