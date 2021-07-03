import os
from common.mapr_logger.log import Log
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class Drill(OperationsBase):
    def __init__(self):
        super(Drill, self).__init__()
        self.drill_dir = os.path.abspath(os.path.join(self.prereq_dir, "drill"))
        if not os.path.exists(self.drill_dir):
            raise NotFoundException(self.drill_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.drill_dir, "drill-namespace.yaml")
        drill_namespace_yaml_file = YamlFile("drill-namespace", "Drill Namespace", file_name, "drill_components", True)
        self.yamls.append(drill_namespace_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-sa.yaml")
        drill_sa_yaml_file = YamlFile("drill-sa", "Drill Service Account", file_name, "drill_components", True)
        self.yamls.append(drill_sa_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-cr.yaml")
        drill_cr_yaml_file = YamlFile("drill-cr", "Drill Cluster Role", file_name, "drill_components", True)
        self.yamls.append(drill_cr_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-role.yaml")
        drill_role_yaml_file = YamlFile("drill-role", "Drill Role", file_name, "drill_components", True)
        self.yamls.append(drill_role_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-crb.yaml")
        drill_crb_yaml_file = YamlFile("drill-crb", "Drill Cluster Role Binding", file_name, "drill_components", True)
        self.yamls.append(drill_crb_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-rb.yaml")
        drill_rb_yaml_file = YamlFile("drill-rb", "Drill Role Binding", file_name, "drill_components", True)
        self.yamls.append(drill_rb_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-imagepullsecret.yaml")
        drill_imagepullsecret_yaml_file = YamlFile("drill-imagepullsecret", "Drill Pull Secret", file_name, "drill_components", True)
        self.yamls.append(drill_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-crd.yaml")
        drill_crd_yaml_file = YamlFile("drill-crd", "Drill CRD", file_name, "drill_components", True)
        self.yamls.append(drill_crd_yaml_file)

        file_name = self.check_exists(self.drill_dir, "drill-deploy-drilloperator.yaml")
        drill_drilloperator_yaml_file = YamlFile("drill-drilloperator", "Drill Operator", file_name, "drill_components", True)
        self.yamls.append(drill_drilloperator_yaml_file)

        # file_name = self.check_exists(self.drill_dir, "drill-scc.yaml")
        # drill_scc_yaml_file = YamlFile("drill-scc", "Drill SCC", file_name, "drill_components", True)
        # self.yamls.append(drill_scc_yaml_file)
        return True

    def install_drill_components(self, upgrade_mode=False):
        installable_yaml_types = ["drill_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)


    def uninstall_drill_components(self):
        uninstallable_yaml_types = ["drill_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

