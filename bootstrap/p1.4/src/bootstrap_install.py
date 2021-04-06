import os

from bootstrapbase import BootstrapBase
from common.const import Constants
from cluster_info import ClusterInfo
from common.mapr_logger.log import Log
from operations.operationsbase import OperationsBase
from mapr.clouds.cloud import Cloud
from validators.openshiftclient_validator import OpenshiftClientValidator
from validators.validator import Validator

from operations.shared import SharedSystem
from operations.csi import CSI
from operations.csinfs import CSINFS
from operations.dataplatform import DataPlatform
from operations.ldap import LDAP
from operations.compute import Compute
from operations.drill import Drill
from operations.kubeflow import Kubeflow
from operations.nodesvc import Nodesvc
from operations.spark import Spark
from operations.autoticket_generator import AutoTicketGenerator
from operations.dataplatform_validator import DataPlatformValidator
from operations.tenant_validator import TenantValidator


class BootstrapInstall(BootstrapBase):
    def __init__(self):
        super(BootstrapInstall, self).__init__(BootstrapBase.INSTALL)
        self.cloud_instance = None
        self.cloud_created = False
        self._parse_args()

    def run(self):
        super(BootstrapInstall, self).run()
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

        if not self.core_install_enabled:
            self.core_install_enabled = self.parsed_args.core_install
        do_cloud_install = self.parsed_args.cloud_install

        do_storage = True
        do_compute = True

        do_drill = self.parsed_args.drill_install
        if do_drill:
            Log.info("Drill installation is enabled", stdout=True)

        do_open_shift = self.parsed_args.openshift_install
        if do_open_shift:
            Log.info("Openshift installation is enabled", stdout=True)

        setup_only = self.parsed_args.setup_only
        if setup_only:
            BootstrapBase.exit_application(0)

        force_stdcsi = self.parsed_args.std_csimount
        force_ecpcsi = self.parsed_args.ecp_csimount

        do_airgap = True
        do_fakelabels = True
        do_csi = True
        install_csi = False
        install_compute = False
        do_compute_templates = False
        install_compute_templates = True
        do_external = False
        install_external = True
        do_secure = False
        install_secure = True
        do_kubeflow = True
        install_kubeflow = True
        do_spark = True
        install_spark = True
        install_storage = False
        do_storage_templates = False
        install_storage_templates = True
        install_drill = do_drill
        install_autoticket_generator = True
        install_dataplatform_validator = True
        install_tenant_validator = True

        if do_cloud_install:
            self.install_cloud()
        self.check_laptop_tools()
        if do_open_shift:
            self.is_openshift_env(k8s)
        if do_csi:
            if self.check_if_csi():
                install_csi = True
                cluster_info = ClusterInfo()
                if force_stdcsi:
                    kdir = Constants.KUBELET_DIR
                elif force_ecpcsi:
                    kdir = Constants.ECP_KUBELET_DIR
                else:
                    kdir = Constants.KUBELET_DIR
                    is_ecp = cluster_info.is_ecp53()
                    if is_ecp:
                        kdir = Constants.ECP_KUBELET_DIR
                OperationsBase.kubelet_directory = kdir
                OperationsBase.replace_dict["{kubelet-dir}"] = OperationsBase.kubelet_directory
        if do_compute:
            install_compute = self.check_if_compute()
            # TODO: fix to automatically check if already installed and avoid
            if install_compute:
                if do_compute_templates:
                    install_compute_templates = self.check_if_compute_templates()
                if do_spark:
                    install_spark = self.check_if_spark()
        if do_kubeflow:
            install_kubeflow = self.check_if_kubeflow()

        if do_storage:
            install_storage = self.check_if_storage()
            # TODO: fix to automatically check if already installed and avoid
            if do_storage_templates:
                install_storage_templates = self.check_if_storage_templates()

        # TODO: fix to automatically check if already installed and avoid
        if do_external:
            install_external = self.check_if_external()
        # TODO: fix to automatically check if secure namespace already installed and avoid
        if do_secure:
            install_secure = self.check_if_secure()

        self.configure_kubernetes(self.cloud_instance)

        if not ldap.check_auth_type():
            return
        install_exampleldap = (ldap.auth_type == Constants.AUTH_TYPES.EXAMPLE_LDAP)

        if do_airgap:
            if self.check_if_airgapped():
                self.airgap_location()

        OperationsBase.replace_dict["{operator-repo}"] = OperationsBase.operator_repo
        OperationsBase.replace_dict["{csi-repo}"] = OperationsBase.csi_repo
        OperationsBase.replace_dict["{kdf-repo}"] = OperationsBase.kdf_rep
        OperationsBase.replace_dict["{kubeflow-repo}"] = OperationsBase.kubeflow_repo
        OperationsBase.replace_dict["{local-path-provisioner-repo}"] = OperationsBase.local_path_provisioner_repo
        OperationsBase.replace_dict["{kfctl-hcp-istio-repo}"] = OperationsBase.kfctl_hcp_istio_repo
        OperationsBase.replace_dict["{busybox-repo}"] = OperationsBase.busybox_repo

        if do_fakelabels:
            fake_labels = self.check_if_fakelabels()
            if not fake_labels:
                OperationsBase.fake_labels = "false"

        OperationsBase.replace_dict["{fake-labels}"] = OperationsBase.fake_labels

        if not self.check_ready():
            return

        if install_compute or install_storage:
            nodesvc.install_nodesvc()
            shared.install_common_components()
        elif install_kubeflow:
            shared.install_common_components()

        if install_secure:
            shared.install_secure_components()
            # LDAP holds the system user secret info
            ldap.install_secure_components()

        if install_exampleldap:
            ldap.install_exampleldap()

        if install_storage:
            dataplatform.install_dataplatform(install_templates=install_storage_templates)

        if install_csi:
            csi.install_csi_components()
            csinfs.install_csi_components()

        if install_external:
            shared.install_external_components()

        if install_compute:
            compute.install_compute_components(install_templates=install_compute_templates)
            if install_spark:
                spark.install_spark_components()
            if install_drill:
                drill.install_drill_components()
            if install_autoticket_generator:
                autoticket_generator.run_install()
            if install_tenant_validator:
                tenant_validator.run_install()
        if install_kubeflow:
            kubeflow.install_kubeflow_components()

        if install_storage:
            if install_dataplatform_validator:
                dataplatform_validator.run_install()

        self.complete_installation()

    def is_cloud_env(self, k8s, is_cloud):
        # Don't ask any cloud questions when we created a cloud env
        if is_cloud:
            return True
        if k8s.is_openshift:
            return False
        print(os.linesep)
        # Check if this is cloud environment
        is_cloud = self.check_if_cloud()
        if is_cloud:
            return True
        return False

    def is_openshift_env(self, k8s):
        print(os.linesep)
        # Check if this is openshift environment
        is_openshift = self.check_if_openshift()
        if is_openshift:
            # Check if oc client installed for openshift operations
            self.check_oc_installed()
            k8s.is_openshift = True

    def check_if_storage(self):
        print(os.linesep)
        agree = self._prompts.prompt_boolean("Install Data Platform?", True, key_name="CREATE_STORAGE")
        return agree

    def check_if_compute(self):
        print(os.linesep)
        agree = self._prompts.prompt_boolean("Install Compute Components?", True, key_name="CREATE_COMPUTE")
        return agree

    def check_if_airgapped(self):
        print(os.linesep)
        agree = self._prompts.prompt_boolean("Use Airgapped Docker Registry? Note: All bootstrap containers must exist in airgap registry!", False, key_name="USE_AIRGAP")
        return agree

    def airgap_location(self):
        registry = self._prompts.prompt("Airgapped Registry Location?", Constants.OPERATOR_REPO, False, key_name="AIRGAP_REGISTRY")
        OperationsBase.csi_repo = registry
        OperationsBase.kdf_rep = registry
        OperationsBase.kubeflow_repo = registry
        OperationsBase.operator_repo = registry
        OperationsBase.local_path_provisioner_repo = registry + '/'
        OperationsBase.kfctl_hcp_istio_repo = registry
        OperationsBase.busybox_repo = registry + '/'

    def check_if_fakelabels(self):
        print(os.linesep)
        fake = self._prompts.prompt_boolean("Label nodes without Ezmeral Container Platform assistance? Note: This is unsupported!", True, key_name="FAKE_LABELS")
        return fake

    def validate_nodes(self):
        print(os.linesep)
        Log.info("We must validate your Kubernetes nodes. "
                 "Node validation and service pods will be installed.", stdout=True)
        agree = self._prompts.prompt_boolean("Do you agree?", True, key_name="AGREEMENT_VALIDATE")
        if not agree:
            Log.error("Exiting due to non-agreement...")
            BootstrapBase.exit_application(2)
        # TODO: Add node exclusion code here
        # exclude = self._prompts.prompt_boolean("Do you want to exclude any nodes?", False, key_name="EXCLUDE_NODES")
        # if exclude:
        #    Log.error("Operation not currently supported...")
        #    BootstrapBase.exit_application(6)

    @staticmethod
    def check_oc_installed():
        oc_validator = OpenshiftClientValidator()
        oc_validator.collect()

        if oc_validator.operation != Validator.OPERATION_OK:
            BootstrapBase.exit_application(5)

    def check_if_cloud(self):
        # TODO: Replace with code to automatically detect if EKS, AKS, or GKE
        choice = self._prompts.prompt_boolean("Installing to a previously created cloud environment?", True,
                                              key_name="CLOUD_ENV")
        return choice

    def check_if_openshift(self):
        # TODO: Replace with code to automatically detect openshift
        choice = self._prompts.prompt_boolean("Installing to an Openshift environment?", False,
                                              key_name="OPENSHIFT_ENV")
        return choice

    def check_if_csi(self):
        choice = self._prompts.prompt_boolean("Install Ezmeral Data Fabric CSI driver?", True, key_name="INSTALL_CSI")
        return choice

    def check_if_spark(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Install Spark Operator?", True, key_name="INSTALL_SPARK")
        return choice

    def check_if_kubeflow(self):
        # TODO: Add code to sense existing operator and upgrade if avail. Keep question
        choice = self._prompts.prompt_boolean("Install Kubeflow Components?", False, key_name="INSTALL_KUBEFLOW")
        return choice

    def check_if_compute_templates(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Install compute CM and Sercret templates?", True, key_name="INSTALL_CONFIG")
        return choice

    def check_if_storage_templates(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Install storage CM and Secret templates?", True, key_name="INSTALL_CONFIG")
        return choice

    def check_if_external(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Install external cluster info namespace?", True, key_name="INSTALL_EXTERNAL")
        return choice

    def check_if_secure(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Install secure info namespace?", True, key_name="INSTALL_SECURE")
        return choice

    def install_cloud(self):
        print("")
        Cloud.initialize(self._prompts)
        cloud_names = Cloud.get_cloud_names()

        if len(cloud_names) == 0:
            Log.warning("There are no supported cloud providers found in this bootstrapper application")
            return False

        Log.info("If you are installing in a cloud provider, we can help you create your kubernetes environment.", True)
        Log.info("ATTENTION: Cloud Environment installation is provided AS IS with no support.", True)
        Log.info("Work with your IT Team to help create kubernetes environments with the security and reliability "
                 "features that suit your enterprise needs.", True)

        create = self._prompts.prompt_boolean("Create a new Kubernetes cluster environment in the Cloud?", False,
                                              key_name="CREATE_CLOUD_ENV")
        if not create:
            Log.info("Not building cloud environment")
            return False

        # Check the availability of each enabled cloud provider
        Cloud.check_available()
        cloud_names = Cloud.get_cloud_names()
        if len(cloud_names) == 0:
            Log.error("Some clouds were enabled but necessary modules that support these clouds are not available")
            BootstrapBase.exit_application(7)

        choice = self._prompts.prompt_choices("Choose a cloud provider", Cloud.get_cloud_names(),
                                              key_name="CLOUD_PROVIDER")

        Log.info("Using cloud provider {0}".format(choice))
        self.cloud_instance = Cloud.get_instance(choice)
        Log.debug("Using cloud instance {0}".format(str(self.cloud_instance)))

        Log.info("Building {0} cloud k8s...".format(choice))
        self.cloud_instance.setup_cloud_usage()
        self.cloud_instance.build_cloud()
        Log.info("Created {0} cloud k8s".format(choice))
        self.cloud_created = True
        return True


if __name__ == '__main__':
    bootstrap_install = BootstrapInstall()
    try:
        bootstrap_install.run()
    except Exception as e:
        Log.exception(e)
        raise e
    BootstrapBase.exit_application(0)
