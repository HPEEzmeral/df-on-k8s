import os

from bootstrapbase import BootstrapBase
from cluster_info import ClusterInfo
from common.const import Constants
from common.mapr_logger.log import Log
from operations.dataplatform_validator import DataPlatformValidator
from operations.operationsbase import OperationsBase

from operations.shared import SharedSystem
from operations.csi import CSI
from operations.csinfs import CSINFS
from operations.dataplatform import DataPlatform
from operations.ldap import LDAP
from operations.compute import Compute
from operations.kubeflow import Kubeflow
from operations.nodesvc import Nodesvc
from operations.spark import Spark
from operations.spark_old import SparkOld
from operations.autoticket_generator import AutoTicketGenerator
from operations.tenant_validator import TenantValidator


class BootstrapUpgrade(BootstrapBase):
    def __init__(self):
        super(BootstrapUpgrade, self).__init__(BootstrapBase.UPGRADE)
        self._parse_args()

    def run(self):
        super(BootstrapUpgrade, self).run()
        k8s = OperationsBase()
        k8s.load_replace_dict()
        shared = SharedSystem()
        nodesvc = Nodesvc()
        csi = CSI()
        nfscsi = CSINFS()
        ldap = LDAP(self._prompts)
        dataplatform = DataPlatform()
        compute = Compute()
        spark = Spark()
        spark_old = SparkOld()
        autoticket_generator = AutoTicketGenerator()
        dataplatform_validator = DataPlatformValidator()
        tenant_validator = TenantValidator()
        kubeflow = Kubeflow()

        force_stdcsi = self.parsed_args.std_csimount
        force_ecpcsi = self.parsed_args.ecp_csimount

        self.prologue()
        self.python_check()

        cluster_info = ClusterInfo()

        do_airgap = True
        do_compute = True
        do_kubeflow = False
        install_kubeflow = False
        do_spark = True
        install_spark = True
        remove_old_spark = False
        install_autoticket_generator = True
        install_tenant_validator = True

        self.check_laptop_tools()
        self.configure_kubernetes()
        cluster_info.examine_cluster(False)

        print("")
        Log.info("Cluster details:", stdout=True)
        is_ecp = cluster_info.is_ecp53()
        if is_ecp:
            Log.info("  Cluster type: Ezmeral Container Platform", stdout=True)
        else:
            Log.info("  Cluster type: Vanilla", stdout=True)
        install_storage = cluster_info.is_data_fabric_installed()
        Log.info("  Data Fabric Installed: " + str(install_storage), stdout=True)
        install_compute = cluster_info.is_compute_installed()
        Log.info("  Compute Installed: " + str(install_compute), stdout=True)
        install_exampleldap = cluster_info.is_ldap_installed()
        Log.info("  Example LDAP Installed: " + str(install_exampleldap), stdout=True)
        do_csi = cluster_info.is_csi_installed()
        Log.info("  CSI Installed: " + str(do_csi), stdout=True)
        Log.info("  Spark Installed: " + str(cluster_info.is_spark_installed()), stdout=True)
        install_dataplatform_validator = install_storage

        if do_csi:
            install_csi = self.check_if_csi()
            if install_csi:
                if force_stdcsi:
                    kdir = Constants.KUBELET_DIR
                elif force_ecpcsi:
                    kdir = Constants.ECP_KUBELET_DIR
                else:
                    kdir = Constants.KUBELET_DIR
                    if is_ecp:
                        kdir = Constants.ECP_KUBELET_DIR
                OperationsBase.kubelet_directory = kdir
                OperationsBase.replace_dict["{kubelet-dir}"] = OperationsBase.kubelet_directory

        if do_compute:
            if do_spark:
                install_spark = cluster_info.is_spark_installed() | cluster_info.is_hpe_spark_in_old_ns()
                remove_old_spark = install_spark & cluster_info.is_hpe_spark_in_old_ns()
                if cluster_info.is_spark_old_ns_exists() and cluster_info.is_hpe_spark_in_old_ns() is False:
                    remove_old_spark = self._prompts.prompt_boolean("Cannot determine operator type in 'spark-operator' namespace. Is it hpe-spark-operator in 'spark-operator' namespace?", True, key_name="REMOVE_SPARK_HPE")

        if do_kubeflow:
            install_kubeflow = self.check_if_kubeflow()

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
        OperationsBase.replace_dict["{fake-labels}"] = "true"

        if not self.check_ready():
            return

        nodesvc.install_nodesvc(True)
        shared.install_common_components(True)

        if install_exampleldap:
            ldap.install_exampleldap(True)

        if install_storage:
            dataplatform.install_dataplatform(True)

        if install_csi:
            csi.install_csi_components(True)
            nfscsi.install_csi_components(True)

        if install_compute:
            compute.install_compute_components(True, True)
            if install_spark:
                if remove_old_spark:
                    spark_old.uninstall_spark_components()
                    spark.install_spark_components()
                else:
                    spark.install_spark_components(True)
            if install_autoticket_generator:
                autoticket_generator.run_install(True)
            if install_tenant_validator:
                tenant_validator.run_install(True)
        if install_kubeflow:
            kubeflow.install_kubeflow_components(True)

        if install_storage:
            if install_dataplatform_validator:
                dataplatform_validator.run_install(True)

        print("")
        cluster_info.examine_cluster(True)
        Log.info(str(cluster_info), stdout=True)

        self.complete_installation()

    def check_if_airgapped(self):
        print(os.linesep)
        agree = self._prompts.prompt_boolean("Use Airgapped Docker Registry? Note: All bootstrap containers must exist in airgap registry!", False, key_name="USE_AIRGAP")
        return agree

    def airgap_location(self):
        print(os.linesep)
        registry = self._prompts.prompt("Airgapped Registry Location?", Constants.OPERATOR_REPO, False, key_name="AIRGAP_REGISTRY")
        OperationsBase.csi_repo = registry
        OperationsBase.kdf_rep = registry
        OperationsBase.kubeflow_repo = registry
        OperationsBase.operator_repo = registry
        OperationsBase.kfctl_hcp_istio_repo = registry
        OperationsBase.busybox_repo = registry + '/'

    def check_if_csi(self):
        Log.warn("Updating the CSI driver is a disruptive operation. All pods using CSI will need to be restarted manually. If the objectstore pod is running, it will also need to be restarted manually.", update_count=False)
        choice = self._prompts.prompt_boolean("Update Ezmeral Data Fabric CSI driver?", True, key_name="INSTALL_CSI")
        return choice

    def check_if_spark(self):
        # TODO: Replace with code to sense existing operator and offer to upgrade
        choice = self._prompts.prompt_boolean("Update Spark Operator?", True, key_name="INSTALL_SPARK")
        return choice

    def check_if_kubeflow(self):
        # TODO: Add code to sense existing operator and upgrade if avail. Keep question
        choice = self._prompts.prompt_boolean("Update Kubeflow Operator?", False, key_name="INSTALL_KUBEFLOW")
        return choice


if __name__ == '__main__':
    bootstrap_upgrade = BootstrapUpgrade()
    try:
        bootstrap_upgrade.run()
    except Exception as e:
        Log.exception(e)
        raise e
    BootstrapBase.exit_application(0)
