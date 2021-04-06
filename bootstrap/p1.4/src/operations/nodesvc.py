import os
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class Nodesvc(OperationsBase):
    def __init__(self):
        super(Nodesvc, self).__init__()
        self.nodesvc_dir = os.path.abspath(os.path.join(self.prereq_dir, "nodesvc"))
        if not os.path.exists(self.nodesvc_dir):
            raise NotFoundException(self.nodesvc_dir)
        self.load_yamls()

    def load_yamls(self):
        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-namespace.yaml")
        nodesvc_namespace_yaml_file = YamlFile("nodesvc-namespace", "Node Service Namespace", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_namespace_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-sa.yaml")
        nodesvc_sa_yaml_file = YamlFile("nodesvc-sa", "Node Service Service Account", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_sa_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-cr.yaml")
        nodesvc_cr_yaml_file = YamlFile("nodesvc-cr", "Node Service ClusterRole", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_cr_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-crb.yaml")
        nodesvc_crb_yaml_file = YamlFile("nodesvc-crb", "Node Service ClusterRoleBinding", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_crb_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-role.yaml")
        nodesvc_role_yaml_file = YamlFile("nodesvc-role", "Node Service Role", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_role_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-rb.yaml")
        nodesvc_rb_yaml_file = YamlFile("nodesvc-rb", "Node Service RoleBinding", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_rb_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-imagepullsecret.yaml")
        nodesvc_imagepullsecret_yaml_file = YamlFile("nodesvc-imagepullsecret", "secret to pull images for Node Service", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.nodesvc_dir, "nodesvc-deploy.yaml")
        nodesvc_deploy_yaml_file = YamlFile("nodesvc-deploy", "Node Service", file_name, "nodesvc_components")
        self.yamls.append(nodesvc_deploy_yaml_file)

        return True

    def install_nodesvc(self, upgrade_mode=False):
        installable_yaml_types = ["nodesvc_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_nodesvc(self):
        uninstallable_yaml_types = ["nodesvc_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
