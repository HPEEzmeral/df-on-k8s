import os

from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class Compute(OperationsBase):
    def __init__(self):
        super(Compute, self).__init__()
        self.system_compute = os.path.abspath(os.path.join(self.prereq_dir, "system-compute"))
        if not os.path.exists(self.system_compute):
            raise NotFoundException(self.system_compute)
        self.template_compute = os.path.abspath(os.path.join(self.customize_dir, "templates-compute"))
        if not os.path.exists(self.template_compute):
            raise NotFoundException(self.template_compute)
        self.template_compute_setup = os.path.abspath(os.path.join(self.prereq_dir, "templates-compute"))
        if not os.path.exists(self.template_compute_setup):
            raise NotFoundException(self.template_compute_setup)
        self.load_yaml_dict()

    def load_yaml_dict(self):

        file_name = self.check_exists(self.system_compute, "system-sa-tenant.yaml")
        system_sa_tenant_yaml_file = YamlFile("system-sa-tenant", "Tenant Operator Service Account", file_name, "system_compute_components")
        self.yamls.append(system_sa_tenant_yaml_file)

        file_name = self.check_exists(self.system_compute, "system-cr-tenant.yaml")
        system_cr_tenant_yaml_file = YamlFile("system-cr-tenant", "Tenant Operator ClusterRole", file_name, "system_compute_components")
        self.yamls.append(system_cr_tenant_yaml_file)

        file_name = self.check_exists(self.system_compute, "system-crb-tenant.yaml")
        system_crb_tenant_yaml_file = YamlFile("system-crb-tenant", "Tenant Operator ClusterRoleBinding", file_name, "system_compute_components")
        self.yamls.append(system_crb_tenant_yaml_file)

        file_name = self.check_exists(self.system_compute, "system-crd-tenantoperator.yaml")
        system_crd_tenant_yaml_file = YamlFile("system-crd-tenant", "Tenant Operator CRD", file_name, "system_compute_components")
        self.yamls.append(system_crd_tenant_yaml_file)

        file_name = self.check_exists(self.system_compute, "system-deploy-tenantoperator.yaml")
        system_tenantoperator_yaml_file = YamlFile("system-tenantoperator", "Tenant Operator", file_name, "system_compute_components")
        self.yamls.append(system_tenantoperator_yaml_file)

        file_name = self.check_exists(self.template_compute_setup, "template-namespace.yaml")
        template_namespace_yaml_file = YamlFile("template-namespace", "Compute Templates Namespace", file_name, "compute_templates")
        self.yamls.append(template_namespace_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-hivemeta-cm.yaml")
        template_hivemeta_cm_yaml_file = YamlFile("template-hivemeta-cm", "Compute Templates Hive Metastore CM", file_name, "compute_templates")
        self.yamls.append(template_hivemeta_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-sparkhistory-cm.yaml")
        template_sparkhistory_cm_yaml_file = YamlFile("template-sparkhistory-cm", "Compute Templates Spark History CM", file_name, "compute_templates")
        self.yamls.append(template_sparkhistory_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-sparkthrift-cm.yaml")
        template_sparkthrift_cm_yaml_file = YamlFile("template-sparkthrift-cm", "Compute Templates Spark Thrift CM", file_name, "compute_templates")
        self.yamls.append(template_sparkthrift_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-sparkmaster-cm.yaml")
        template_sparkmaster_cm_yaml_file = YamlFile("template-sparkmaster-cm", "Compute Templates Spark Master CM", file_name, "compute_templates")
        self.yamls.append(template_sparkmaster_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-sparkworker-cm.yaml")
        template_sparkworker_cm_yaml_file = YamlFile("template-sparkworker-cm", "Compute Templates Spark Master CM", file_name, "compute_templates")
        self.yamls.append(template_sparkworker_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-sparkuiproxy-cm.yaml")
        template_sparkuiproxy_cm_yaml_file = YamlFile("template-sparkuiproxy-cm", "Compute Templates Spark UI Proxy CM", file_name, "compute_templates")
        self.yamls.append(template_sparkuiproxy_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-livy-cm.yaml")
        template_livy_cm_yaml_file = YamlFile("template-livy-cm", "Compute Templates Livy CM", file_name, "compute_templates")
        self.yamls.append(template_livy_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-tenantcli-cm.yaml")
        template_tenantcli_cm_yaml_file = YamlFile("template-tenantcli-cm", "Compute Templates Tenant CLI CM", file_name, "compute_templates")
        self.yamls.append(template_tenantcli_cm_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-psp-tenant.yaml")
        template_psp_tenant_yaml_file = YamlFile("template-psp-tenant", "Compute Templates Pod Security Policy", file_name, "compute_templates")
        self.yamls.append(template_psp_tenant_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-role-tenant.yaml")
        template_role_tenant_yaml_file = YamlFile("template-role-tenant", "Compute Templates Tenant Role", file_name, "compute_templates")
        self.yamls.append(template_role_tenant_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-role-tenantcli.yaml")
        template_role_tenantcli_yaml_file = YamlFile("template-role-tenantcli", "Compute Templates Tenant CLI Role", file_name, "compute_templates")
        self.yamls.append(template_role_tenantcli_yaml_file)

        file_name = self.check_exists(self.template_compute, "template-role-tenant-user.yaml")
        template_role_tenant_user_yaml_file = YamlFile("template-role-tenant-user", "Compute Templates Tenant User Role", file_name, "compute_templates")
        self.yamls.append(template_role_tenant_user_yaml_file)

        # file_name = self.check_exists(self.template_compute, "system-scc-tenant.yaml")
        # system_scc_tenant_yaml_file = YamlFile("system-scc-tenant", "SCC", file_name, "compute_templates", True)
        # self.yamls.append(system_scc_tenant_yaml_file)

        return True

    def install_compute_components(self, upgrade_mode=False, install_templates=False):
        installable_yaml_types = ["system_compute_components"]
        if install_templates:
            installable_yaml_types.append("compute_templates")
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_compute_components(self, uninstall_templates=False):
        uninstallable_yaml_types = ["system_compute_components"]
        if uninstall_templates:
            uninstallable_yaml_types.append("compute_templates")
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
