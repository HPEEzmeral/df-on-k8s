import os

from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class CSI(OperationsBase):
    def __init__(self):
        super(CSI, self).__init__()
        self.csi_dir = os.path.abspath(os.path.join(self.prereq_dir, "csi"))
        if not os.path.exists(self.csi_dir):
            raise NotFoundException(self.csi_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.csi_dir, "csi-namespace.yaml")
        csi_namespace_yaml_file = YamlFile("csi-namespace", "CSI Namespace", file_name, "csi_components")
        self.yamls.append(csi_namespace_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-nodeplugin-sa.yaml")
        csi_nodeplugin_sa_yaml_file = YamlFile("csi-nodeplugin-sa", "CSI Node Plugin Service Account", file_name, "csi_components")
        self.yamls.append(csi_nodeplugin_sa_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-controller-sa.yaml")
        csi_controller_sa_yaml_file = YamlFile("csi-controller-sa", "CSI Controller Service Account", file_name, "csi_components")
        self.yamls.append(csi_controller_sa_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-attacher-cr.yaml")
        csi_attacher_cr_yaml_file = YamlFile("csi-attacher-cr", "CSI Attacher Cluster Role", file_name, "csi_components")
        self.yamls.append(csi_attacher_cr_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-attacher-crb.yaml")
        csi_attacher_crb_yaml_file = YamlFile("csi-attacher-crb", "CSI Attacher Cluster Role Binding", file_name, "csi_components")
        self.yamls.append(csi_attacher_crb_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-nodeplugin-cr.yaml")
        csi_nodeplugin_cr_yaml_file = YamlFile("csi-nodeplugin-cr", "CSI Node Plugin Cluster Role", file_name, "csi_components")
        self.yamls.append(csi_nodeplugin_cr_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-nodeplugin-crb.yaml")
        csi_nodeplugin_crb_yaml_file = YamlFile("csi-nodeplugin-crb", "CSI Node Plugin Cluster Role Binding", file_name, "csi_components")
        self.yamls.append(csi_nodeplugin_crb_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-controller-cr.yaml")
        csi_controller_cr_yaml_file = YamlFile("csi-controller-cr", "CSI Controller Cluster Role", file_name, "csi_components")
        self.yamls.append(csi_controller_cr_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-controller-crb.yaml")
        csi_controller_crb_yaml_file = YamlFile("csi-controller-crb", "CSI Controller Cluster Role Binding", file_name, "csi_components")
        self.yamls.append(csi_controller_crb_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-imagepullsecret.yaml")
        csi_imagepullsecret_yaml_file = YamlFile("csi-imagepullsecret", "secret to pull images for CSI", file_name, "csi_components")
        self.yamls.append(csi_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-deploy-nodeplugin.yaml")
        csi_nodeplugin_yaml_file = YamlFile("csi-nodeplugin", "CSI NodePlugin DaemonSet", file_name, "csi_components")
        self.yamls.append(csi_nodeplugin_yaml_file)

        file_name = self.check_exists(self.csi_dir, "csi-deploy-controller.yaml")
        csi_controller_yaml_file = YamlFile("csi-controller", "CSI Controller StatefulSet", file_name, "csi_components")
        self.yamls.append(csi_controller_yaml_file)

        # file_name = self.check_exists(self.csi_dir, "csi-deploy-openshift-nodeplugin.yaml")
        # csi_openshift_nodeplugin_yaml_file = YamlFile("csi-controller", "CSI Openshift Node plugin", file_name, "csi_components", True)
        # self.yamls.append(csi_openshift_nodeplugin_yaml_file)

        # file_name = self.check_exists(self.csi_dir, "csi-deploy-openshift-controller.yaml")
        # csi_openshift_controller_yaml_file = YamlFile("csi-controller", "CSI Openshift Node plugin", file_name, "csi_components", True)
        # self.yamls.append(csi_openshift_controller_yaml_file)

        # file_name = self.check_exists(self.csi_dir, "csi-scc.yaml")
        # csi_scc_yaml_file = YamlFile("csi-scc", "CSI SCC", file_name, "csi_components", True)
        # self.yamls.append(csi_scc_yaml_file)

        return True

    def install_csi_components(self, upgrade_mode=False):
        installable_yaml_types = ["csi_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_csi_components(self):
        uninstallable_yaml_types = ["csi_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
