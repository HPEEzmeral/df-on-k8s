import os

from bootstrapbase import BootstrapBase
from common.const import Constants
from common.mapr_logger.log import Log
from operations.operationsbase import OperationsBase
from operations.shared import SharedSystem
from operations.csi import CSI
from operations.csinfs import CSINFS
from operations.dataplatform import DataPlatform
from operations.compute import Compute
from operations.drill import Drill
from operations.ldap import LDAP
from operations.kubeflow import Kubeflow
from operations.nodesvc import Nodesvc
from operations.spark import Spark
from operations.autoticket_generator import AutoTicketGenerator
from operations.dataplatform_validator import DataPlatformValidator
from operations.tenant_validator import TenantValidator


class BootstrapUninstall(BootstrapBase):
    def __init__(self):
        super(BootstrapUninstall, self).__init__(BootstrapBase.UNINSTALL)

        self.cloud_instance = None
        self.cloud_created = False
        self._parse_args()

    def run(self):
        super(BootstrapUninstall, self).run()
        k8s = OperationsBase()
        k8s.load_replace_dict()
        shared = SharedSystem()
        nodesvc = Nodesvc()
        csi = CSI()
        csinfs =  CSINFS()
        ldap = LDAP(self._prompts)
        dataplatform = DataPlatform()
        compute = Compute()
        spark = Spark()
        autoticket_generator = AutoTicketGenerator()
        dataplatform_validator = DataPlatformValidator()
        tenant_validator = TenantValidator()
        kubeflow = Kubeflow()
        # openshift = OpenShift()
        drill = Drill()

        self.prologue()
        self.python_check()
        self.check_laptop_tools()
        self.confirm_delete_installation()

        if self.core_install_enabled:
            do_storage = True
        else:
            do_storage = self.parsed_args.core_uninstall

        do_compute = True
        do_drill = self.parsed_args.drill_uninstall
        do_csi = True
        uninstall_csi = False
        uninstall_compute = False
        # uninstall_autoticket_generator = False
        uninstall_compute_templates = False
        uninstall_storage = False
        uninstall_storage_templates = False
        do_kubeflow = True
        uninstall_kubeflow = True
        do_spark = False
        uninstall_spark = True
        do_external = True
        uninstall_external = False
        do_secure = True
        uninstall_secure = False
        do_exampleldap = True
        uninstall_exampleldap = False
        uninstall_drill = False

        OperationsBase.replace_dict["{operator-repo}"] = Constants.OPERATOR_REPO
        OperationsBase.replace_dict["{csi-repo}"] = Constants.CSI_REPO
        OperationsBase.replace_dict["{kdf-repo}"] = Constants.KDF_REPO
        OperationsBase.replace_dict["{kubeflow-repo}"] = Constants.KUBEFLOW_REPO
        OperationsBase.replace_dict["{local-path-provisioner-repo}"] = Constants.LOCAL_PATH_PROVISIONER_REPO
        OperationsBase.replace_dict["{kfctl-hcp-istio-repo}"] = Constants.KFCTL_HSP_ISTIO_REPO
        OperationsBase.replace_dict["{busybox-repo}"] = Constants.BUSYBOX_REPO
        OperationsBase.replace_dict["{fake-labels}"] = "true"

        if do_csi:
            uninstall_csi = self.check_remove_csi()
        if do_storage:
            uninstall_storage = self.check_remove_storage()
            uninstall_storage_templates = self.check_remove_storage_templates()
        if do_external:
            uninstall_external = self.check_remove_external()
        if do_secure:
            uninstall_secure = self.check_remove_secure()
        if do_exampleldap:
            uninstall_exampleldap = self.check_remove_exampleldap(k8s)
        if do_compute:
            uninstall_compute = self.check_remove_compute()
            # uninstall_autoticket_generator = uninstall_compute
            if uninstall_compute:
                uninstall_compute_templates = self.check_remove_compute_templates()
                if do_spark:
                    uninstall_spark = self.check_remove_spark()
                uninstall_drill = do_drill
        if do_kubeflow:
            uninstall_kubeflow = self.check_remove_kubeflow()

        # Check if the connected k8s environment is Openshift
        # if k8s.is_openshift_connected():
        #     k8s.is_openshift = True
        #     k8s.switch_to_oc()

        if uninstall_external:
            shared.uninstall_external_components()
        if uninstall_storage:
            dataplatform.uninstall_dataplatform(uninstall_templates=uninstall_storage_templates)
            dataplatform_validator.run_uninstall()
        if uninstall_compute:
            compute.uninstall_compute_components(uninstall_templates=uninstall_compute_templates)
            autoticket_generator.run_uninstall()
            tenant_validator.run_uninstall()
            # uninstall_autoticket_generator = uninstall_compute
            if uninstall_spark:
                spark.uninstall_spark_components()
            if uninstall_drill:
                drill.uninstall_drill_components()
        if uninstall_compute or uninstall_storage:
            shared.uninstall_common_components()
            nodesvc.uninstall_nodesvc()
        elif uninstall_kubeflow:
            shared.uninstall_common_components()
        if uninstall_secure:
            shared.uninstall_secure_components()
        if uninstall_exampleldap:
            ldap.uninstall_exampleldap()
        if uninstall_kubeflow:
            kubeflow.uninstall_kubeflow_components()
        if uninstall_csi:
            csi.uninstall_csi_components()
            csinfs.uninstall_csi_components()

        self.complete_uninstallation()

    def confirm_delete_installation(self):
        print(os.linesep)
        Log.info("This will uninstall ALL Ezmeral Data Fabric for Kubernetes operators from your Kubernetes environment. This will cause all "
                 "Tenants to be destroyed. They cannot be recovered!", True)
        agree = self._prompts.prompt_boolean("Do you agree?", False, key_name="AGREEMENT")
        if not agree:
            Log.info("Very wise decision. Exiting uninstall...", True)
            BootstrapBase.exit_application(2)

    def check_remove_csi(self):
        choice = self._prompts.prompt_boolean("Remove the Ezmeral Data Fabric CSI driver?", False, key_name="REMOVE_CSI")
        return choice

    def check_remove_spark(self):
        choice = self._prompts.prompt_boolean("Remove the Spark Operator?", False, key_name="REMOVE_SPARK")
        return choice

    def check_remove_drill(self):
        choice = self._prompts.prompt_boolean("Remove the Drill Operator?", False, key_name="REMOVE_DRILL")
        return choice

    def check_remove_kubeflow(self):
        choice = self._prompts.prompt_boolean("Remove the Kubeflow Operator?", False, key_name="REMOVE_KUBEFLOW")
        return choice

    def check_remove_compute(self):
        choice = self._prompts.prompt_boolean("Remove Compute components?", False, key_name="REMOVE_COMPUTE")
        return choice

    def check_remove_compute_templates(self):
        choice = self._prompts.prompt_boolean("Remove the Compute templates? Note: You will lose your template changes!", False, key_name="REMOVE_COMPUTE_TEMPLATES")
        return choice

    def check_remove_storage(self):
        choice = self._prompts.prompt_boolean("Remove Data Platform?", False, key_name="REMOVE_STORAGE")
        return choice

    def check_remove_storage_templates(self):
        choice = self._prompts.prompt_boolean("Remove the Data Platform Templates? Note: You will lose your template changes!", False, key_name="REMOVE_STORAGE_TEMPLATES")
        return choice

    def check_remove_external(self):
        choice = self._prompts.prompt_boolean("Remove the External Cluster Info? Note: You will lose your imported cluster info!", False, key_name="REMOVE_EXTERNAL_INFO")
        return choice

    def check_remove_secure(self):
        choice = self._prompts.prompt_boolean("Remove the Secure Namespace? Note: You will lose your template changes!", False, key_name="REMOVE_SECURE")
        return choice

    @staticmethod
    def check_remove_exampleldap(k8s):
        get_str = "namespace {0}".format(Constants.EXAMPLE_LDAP_NAMESPACE)
        response, status = k8s.run_get(get_str, False)
        result = (status == 0)
        return result

    def is_cloud_env(self):
        print(os.linesep)
        is_cloud = self._prompts.prompt_boolean("Is this a cloud env?", True, key_name="CLOUD_ENV")
        if is_cloud:
            return True
        return False

    @staticmethod
    def complete_uninstallation():
        print(os.linesep)

        msg = "This Kubernetes environment"
        warnings = Log.get_warning_count()
        errors = Log.get_error_count()

        if errors > 0 and warnings > 0:
            msg = "{0} had {1} error(s) and {2} warning(s) during the uninstall process for selected components".format(msg, errors, warnings)
            Log.error(msg)
        elif errors > 0 and warnings == 0:
            msg = "{0} had {1} error(s) during the uninstall process for selected components".format(msg, errors)
            Log.error(msg)
        elif errors == 0 and warnings > 0:
            msg = "{0} had {1} warnings(s) during the uninstall process for selected components".format(msg, warnings)
            Log.warning(msg)
        else:
            msg = "{0} has had selected components successfully uninstalled".format(msg)
            Log.info(msg, True)

        if errors > 0 or warnings > 0:
            msg = "Please check the bootstrap log file for this session here: {0}".format(Log.get_log_filename())
            Log.warning(msg)

        Log.info("")


if __name__ == '__main__':
    bootstrap_uninstall = BootstrapUninstall()
    try:
        bootstrap_uninstall.run()
    except Exception as e:
        Log.exception(e)
        raise e
    BootstrapBase.exit_application(0)
