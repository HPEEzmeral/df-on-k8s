import os

from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class Kubeflow(OperationsBase):
    def __init__(self):
        super(Kubeflow, self).__init__()
        self.kubeflow_dir = os.path.abspath(os.path.join(self.prereq_dir, "kubeflow"))
        if not os.path.exists(self.kubeflow_dir):
            raise NotFoundException(self.kubeflow_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-namespace.yaml")
        kubeflow_namespace_yaml_file = YamlFile("kubeflow-namespace", "Kubeflow Namespace", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_namespace_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-sa.yaml")
        kubeflow_sa_yaml_file = YamlFile("kubeflow-sa", "Kubeflow Service Account", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_sa_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-sa-localpathprovisioner.yaml")
        kubeflow_sa_localpathprovisioner_yaml_file = YamlFile("kubeflow-sa-localpathprovisioner", "Local Path Provisioner Service Account", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_sa_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-cr.yaml")
        kubeflow_cr_yaml_file = YamlFile("kubeflow-cr", "Kubeflow Cluster Role", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_cr_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-cr-localpathprovisioner.yaml")
        kubeflow_cr_localpathprovisioner_yaml_file = YamlFile("kubeflow-cr-localpathprovisioner", "Local Path Provisioner Cluster Role", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_cr_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-crb.yaml")
        kubeflow_crb_yaml_file = YamlFile("kubeflow-crb", "Kubeflow Cluster Role Binding", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_crb_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-crb-localpathprovisioner.yaml")
        kubeflow_crb_localpathprovisioner_yaml_file = YamlFile("kubeflow-crb-localpathprovisioner", "Local Path Provisioner Cluster Role Binding", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_crb_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-imagepullsecret.yaml")
        kubeflow_imagepullsecret_yaml_file = YamlFile("kubeflow-imagepullsecret", "secret to pull images for Kubeflow", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-crd-kubeflowoperator.yaml")
        kubeflow_crd_kubeflowoperator_yaml_file = YamlFile("kubeflow-crd-kubeflowoperator", "Kubeflow CRD", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_crd_kubeflowoperator_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-deploy-kubeflowoperator.yaml")
        kubeflow_kubeflowoperator_yaml_file = YamlFile("kubeflow-kubeflowoperator", "Kubeflow Operator", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_kubeflowoperator_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-cm-localpathprovisioner.yaml")
        kubeflow_cm_localpathprovisioner_yaml_file = YamlFile("kubeflow-cm-localpathprovisioner", "Local Path Provisioner CM", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_cm_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-deploy-localpathprovisioner.yaml")
        kubeflow_deploy_localpathprovisioner_yaml_file = YamlFile("kubeflow-deploy-localpathprovisioner", "Local Path Provisioner ", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_deploy_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kubeflow-sc-localpathprovisioner.yaml")
        kubeflow_sc_localpathprovisioner_yaml_file = YamlFile("kubeflow-sc-localpathprovisioner", "Local Path Provisioner SC", file_name, "kubeflow_components")
        self.yamls.append(kubeflow_sc_localpathprovisioner_yaml_file)

        file_name = self.check_exists(self.kubeflow_dir, "kfctl_hcp_istio.yaml")
        kfctl_hcp_istio_yaml_file = YamlFile("kfctl_hcp_istio", "Kfctl HCP Istio", file_name, "kubeflow_components")
        self.yamls.append(kfctl_hcp_istio_yaml_file)

        return True

    def install_kubeflow_components(self, upgrade_mode=False):
        if OperationsBase.replace_dict["{kfctl-hcp-istio-repo}"]:
            OperationsBase.replace_dict["{kfctl-hcp-istio-repo}"] += "/"
        else:
            self.copy_hpe_pull_secrets_to_ns("kubeflow")
        self.setup_dex_for_ldap_auth()
        installable_yaml_types = ["kubeflow_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_kubeflow_components(self):
        uninstallable_yaml_types = ["kubeflow_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
