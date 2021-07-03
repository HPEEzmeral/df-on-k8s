import os
import json

from bootstrapbase import BootstrapBase
from common.mapr_logger.log import Log
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class SharedSystem(OperationsBase):
    def __init__(self):
        super(SharedSystem, self).__init__()
        self.external_dir = os.path.abspath(os.path.join(self.prereq_dir, "external"))
        if not os.path.exists(self.external_dir):
            raise NotFoundException(self.external_dir)
        self.secure_dir = os.path.abspath(os.path.join(self.prereq_dir, "secure"))
        if not os.path.exists(self.secure_dir):
            raise NotFoundException(self.secure_dir)
        self.system_common_dir = os.path.abspath(os.path.join(self.prereq_dir, "system-common"))
        if not os.path.exists(self.system_common_dir):
            raise NotFoundException(self.system_common_dir)
        self.load_yamls()

    def load_yamls(self):
        file_name = self.check_exists(self.system_common_dir, "system-namespace.yaml")
        system_namespace_yaml_file = YamlFile("system-namespace", "System Namespace", file_name, "system_common_components")
        self.yamls.append(system_namespace_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-probe-cm.yaml")
        system_namespace_yaml_file = YamlFile("system-probe-cm", "System Probe ConfigMap", file_name, "system_common_components")
        self.yamls.append(system_namespace_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-imagepullsecret.yaml")
        system_imagepullsecret_yaml_file = YamlFile("system-imagepullsecret", "secret to pull images for System", file_name, "system_common_components")
        self.yamls.append(system_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-cr-pv.yaml")
        system_cr_pv_yaml_file = YamlFile("system-cr-pv", "PVCreate ClusterRole", file_name, "system_common_components")
        self.yamls.append(system_cr_pv_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-admin.yaml")
        system_priorityclass_admin_yaml_file = YamlFile("system-priorityclass-admin", "System Priority Class Admin", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_admin_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-dataplatformservices.yaml")
        system_priorityclass_clusterservices_yaml_file = YamlFile("system-priorityclass-clusterservices", "System Priority Class Cluster Services", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_clusterservices_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-compute.yaml")
        system_priorityclass_compute_yaml_file = YamlFile("system-priorityclass-compute", "System Priority Class Compute", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_compute_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-critical.yaml")
        system_priorityclass_critical_yaml_file = YamlFile("system-priorityclass-critical", "System Priority Class Critical", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_critical_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-gateways.yaml")
        system_priorityclass_gateways_yaml_file = YamlFile("system-priorityclass-gateways", "System Priority Class Gateways", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_gateways_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-metrics.yaml")
        system_priorityclass_metrics_yaml_file = YamlFile("system-priorityclass-metrics", "System Priority Class Metrics", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_metrics_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-mfs.yaml")
        system_priorityclass_mfs_yaml_file = YamlFile("system-priorityclass-metrics", "System Priority Class MFS", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_mfs_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-priorityclass-tenantservices.yaml")
        system_priorityclass_tenantservices_yaml_file = YamlFile("system-priorityclass-tenantservices", "System Priority Class Tenant Services", file_name, "system_common_components")
        self.yamls.append(system_priorityclass_tenantservices_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-storageclass-hdd.yaml")
        system_storageclass_hdd_yaml_file = YamlFile("system-storageclass-hdd", "System Storage Class HDD", file_name, "system_common_components")
        self.yamls.append(system_storageclass_hdd_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-storageclass-nvme.yaml")
        system_storageclass_nvme_yaml_file = YamlFile("system-storageclass-nvme", "System Storage Class NVME", file_name, "system_common_components")
        self.yamls.append(system_storageclass_nvme_yaml_file)

        file_name = self.check_exists(self.system_common_dir, "system-storageclass-ssd.yaml")
        system_storageclass_ssd_yaml_file = YamlFile("system-storageclass-ssd", "System Storage Class SSD", file_name, "system_common_components")
        self.yamls.append(system_storageclass_ssd_yaml_file)

        # secure
        file_name = self.check_exists(self.secure_dir, "secure-namespace.yaml")
        secure_namespace_yaml_file = YamlFile("secure-namespace", "Secure Info Namespace", file_name, "secure_components")
        self.yamls.append(secure_namespace_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-imagepullsecret.yaml")
        secure_imagepullsecret_yaml_file = YamlFile("secure-imagepullsecret", "secret to pull images for Secure", file_name, "secure_components")
        self.yamls.append(secure_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-sssdsecret.yaml")
        secure_sssdsecret_yaml_file = YamlFile("secure-sssdsecret", "Secure SSSD Secret", file_name, "secure_components")
        self.yamls.append(secure_sssdsecret_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-sslsecret.yaml")
        secure_sslsecret_yaml_file = YamlFile("secure-sslsecret", "Secure SSL Secret", file_name, "secure_components")
        self.yamls.append(secure_sslsecret_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-sshsecret.yaml")
        secure_sshsecret_yaml_file = YamlFile("secure-sshsecret", "Secure SSH Secret", file_name, "secure_components")
        self.yamls.append(secure_sshsecret_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-csiticketsecret.yaml")
        secure_csiticketsecret_yaml_file = YamlFile("secure-csiticketsecret", "Secure CSI Ticket Secret", file_name, "secure_components")
        self.yamls.append(secure_csiticketsecret_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-ldapclient-cm.yaml")
        secure_ldapclient_cm_yaml_file = YamlFile("secure-ldapclient-cm", "Secure LDAP Client CM", file_name, "secure_components")
        self.yamls.append(secure_ldapclient_cm_yaml_file)

        file_name = self.check_exists(self.secure_dir, "secure-shared-cm.yaml")
        secure_shared_cm_yaml_file = YamlFile("secure-shared-cm", "Secure Shared CM", file_name, "secure_shared_cm_components")
        self.yamls.append(secure_shared_cm_yaml_file)

        # external
        file_name = self.check_exists(self.external_dir, "external-namespace.yaml")
        external_namespace_yaml_file = YamlFile("external-namespace", "External Info Namespace", file_name, "external_components")
        self.yamls.append(external_namespace_yaml_file)

        return True

    def install_common_components(self, upgrade_mode=False):
        installable_yaml_types = ["system_common_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_common_components(self):
        uninstallable_yaml_types = ["system_common_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

    def install_external_components(self, upgrade_mode=False):
        installable_yaml_types = ["external_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_external_components(self):
        uninstallable_yaml_types = ["external_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

    def install_secure_components(self, upgrade_mode=False):
        installable_yaml_types = ["secure_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)
        installable_yaml_types = ["secure_shared_cm_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_secure_components(self):
        # remove the {sharedcm-file-contents} from the file first to avoid surfacing an err
        OperationsBase.replace_dict["{sharedcm-file-contents}"] = ""
        uninstallable_yaml_types = ["secure_components", "secure_shared_cm_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
