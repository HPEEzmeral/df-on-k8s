import os

from bootstrapbase import BootstrapBase, BOOTSTRAP_BUILD_VERSION_NO
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
from operations.existing_df_updater import ExistingDfUpdater
from operations.snapshotter_crds import SnapshotterCRDs


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
        snapshotter_crds = SnapshotterCRDs()
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
        existing_df_updater = ExistingDfUpdater()

        force_stdcsi = self.parsed_args.std_csimount
        force_ecpcsi = self.parsed_args.ecp_csimount

        self.prologue()
        self.python_check()

        OperationsBase.replace_dict["{edf-version}"] = str(BOOTSTRAP_BUILD_VERSION_NO)
        OperationsBase.replace_dict["{tolerate-master-node}"] = ""

        cluster_info = ClusterInfo()

        restart_existing_df = False
        do_airgap = True
        do_compute = True
        do_kubeflow = False
        install_kubeflow = False
        do_spark = True
        remove_spark = True
        remove_old_spark = False
        install_autoticket_generator = True
        install_tenant_validator = True
        install_storage_templates = True
        is_upgradable_df = False
        upgrade_existing_df = False

        self.check_laptop_tools()
        self.configure_kubernetes()
        cluster_info.examine_cluster(False)

        print("")
        Log.info("Cluster details:", stdout=True)
        is_ecp = cluster_info.is_ecp53()
        if is_ecp:
            Log.info("  Cluster type: Ezmeral Container Platform", stdout=True)
        else:
            Log.info("  Cluster type: Non-Ezmeral Kubernetes Deployment", stdout=True)
        install_storage = cluster_info.is_data_fabric_installed()
        Log.info("  Data Fabric Installed: " + str(install_storage), stdout=True)
        install_compute = cluster_info.is_compute_installed()
        Log.info("  Compute Installed: " + str(install_compute), stdout=True)
        install_exampleldap = cluster_info.is_ldap_installed()
        Log.info("  Example LDAP Installed: " + str(install_exampleldap), stdout=True)
        install_csi = False
        do_csi = cluster_info.is_csi_installed()
        Log.info("  CSI Installed: " + str(do_csi), stdout=True)
        Log.info("  Spark Installed: " + str(cluster_info.is_spark_installed()), stdout=True)
        install_dataplatform_validator = install_storage

        if install_storage:
            is_upgradable_df = existing_df_updater.check()
            if is_upgradable_df:
                Log.info("  Existing Data Fabric named {0} detected using baseimagetag {1}".format(existing_df_updater.
                    get_existing_df_name(),existing_df_updater.get_existing_df_baseimagetag()), stdout=True)
            else:
                Log.info("  No existing Data Fabric detected that can be upgraded", stdout=False)

        if do_csi:
            install_csi = self.check_if_csi()
            if install_csi:
                if force_stdcsi:
                    kdir = Constants.KUBELET_DIR
                    Log.info("Forcing CSI Kubelet to standard dir: {0}".format(kdir))
                elif force_ecpcsi:
                    kdir = Constants.ECP_KUBELET_DIR
                    Log.info("Forcing CSI Kubelet to ECP dir: {0}".format(kdir))
                else:
                    kdir = Constants.KUBELET_DIR
                    if is_ecp:
                        kdir = Constants.ECP_KUBELET_DIR
                    Log.info("CSI Kubelet to detected dir: {0}".format(kdir))

                OperationsBase.kubelet_directory = kdir
                OperationsBase.replace_dict["{kubelet-dir}"] = OperationsBase.kubelet_directory

        if do_compute:
            if do_spark:
                remove_spark = cluster_info.is_spark_installed()
                remove_old_spark = cluster_info.is_hpe_spark_in_old_ns()
                if cluster_info.is_spark_old_ns_exists() and cluster_info.is_hpe_spark_in_old_ns() is False:
                    remove_old_spark = self._prompts.prompt_boolean("Cannot determine operator type in 'spark-operator' namespace. Is it hpe-spark-operator in 'spark-operator' namespace?", True, key_name="REMOVE_SPARK_HPE")

        if do_kubeflow:
            install_kubeflow = self.check_if_kubeflow()

        if do_airgap:
            if self.check_if_airgapped():
                self.airgap_location()

        if is_upgradable_df:
            upgrade_existing_df = self._prompts.prompt_boolean("Do you want to also take the Data Fabric named "
                                    "{0}".format(existing_df_updater.get_existing_df_name()) +
                                    " offline and have it upgraded at this time?", False, key_name="UPGRADE_EXISTING_DF")
            if upgrade_existing_df:
                restart_existing_df = self._prompts.prompt_boolean("Would you like the Data Fabric to restart "
                                         "automatically after it is upgraded?  Keep it offline if you are going to "
                                         "perform any other major upgrades next such as upgrading Kubernetes.",
                                         True, key_name="RESTART_EXISTING_DF")


        str_tolerations = ""
        if cluster_info.schedule_pods_on_master:
            str_tolerations = "\n        - key: node-role.kubernetes.io/master\n          operator: Exists\n          effect: NoSchedule"
        OperationsBase.replace_dict["{tolerate-master-node}"] = str_tolerations
        OperationsBase.replace_dict["{operator-repo}"] = OperationsBase.operator_repo
        OperationsBase.replace_dict["{csi-repo}"] = OperationsBase.csi_repo
        OperationsBase.replace_dict["{kdf-repo}"] = OperationsBase.kdf_rep
        OperationsBase.replace_dict["{kubeflow-repo}"] = OperationsBase.kubeflow_repo
        OperationsBase.replace_dict["{local-path-provisioner-repo}"] = OperationsBase.local_path_provisioner_repo
        OperationsBase.replace_dict["{kfctl-hcp-istio-repo}"] = OperationsBase.kfctl_hcp_istio_repo
        OperationsBase.replace_dict["{busybox-repo}"] = OperationsBase.busybox_repo
        OperationsBase.replace_dict["{fake-labels}"] = "true"
        OperationsBase.replace_dict["{fake-labels-disk-lists}"] = ""

        if not self.check_ready():
            return

        nodesvc.install_nodesvc(True)
        shared.install_common_components(True)

        if install_exampleldap:
            ldap.install_exampleldap(True)

        if install_storage:
            dataplatform.install_dataplatform(upgrade_mode=True, install_templates=install_storage_templates)

        if install_csi:
            snapshotter_crds.install_snapshottercrd_components(True)
            csi.install_csi_components(True)
            nfscsi.install_csi_components(True)

        if install_compute:
            compute.install_compute_components(True, True)
            if remove_spark:
                Log.info("Uninstalling cluster level spark operator. ")
                spark.uninstall_spark_components()
            if remove_old_spark:
                Log.info("Uninstalling cluster level spark operator. ")
                spark_old.uninstall_spark_components()
            if install_autoticket_generator:
                autoticket_generator.run_install(True)
            if install_tenant_validator:
                tenant_validator.run_install(True)
        if install_kubeflow:
            kubeflow.install_kubeflow_components(True)

        if install_storage:
            if install_dataplatform_validator:
                dataplatform_validator.run_install(True)

        if upgrade_existing_df:
            successful_existing_upgrade = existing_df_updater.run_update(restart_existing_df)
            if not successful_existing_upgrade and restart_existing_df:
                Log.info("The Data Fabric was upgraded but remains offline. To bring it back online run "
                         "'edf startup resume' in it's admincli-0 pod.")

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
        print(os.linesep)
        Log.warn("Updating the CSI driver is a disruptive operation. All pods using CSI will need to be restarted manually. If the objectstore pod is running, it will also need to be restarted manually.", update_count=False)
        choice = self._prompts.prompt_boolean("Update Ezmeral Data Fabric CSI driver?", True, key_name="INSTALL_CSI")
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
