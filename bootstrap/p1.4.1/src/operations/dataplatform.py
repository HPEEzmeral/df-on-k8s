import os

from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class DataPlatform(OperationsBase):
    def __init__(self):
        super(DataPlatform, self).__init__()
        self.system_dataplatform = os.path.abspath(os.path.join(self.prereq_dir, "system-dataplatform"))
        if not os.path.exists(self.system_dataplatform):
            raise NotFoundException(self.system_dataplatform)
        self.templates_dataplatform = os.path.abspath(os.path.join(self.customize_dir, "templates-dataplatform"))
        if not os.path.exists(self.templates_dataplatform):
            raise NotFoundException(self.templates_dataplatform)
        self.templates_dataplatform_setup = os.path.abspath(os.path.join(self.prereq_dir, "templates-dataplatform"))
        if not os.path.exists(self.templates_dataplatform_setup):
            raise NotFoundException(self.templates_dataplatform_setup)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.system_dataplatform, "system-sa-dataplatform.yaml")
        system_sa_dataplatform_yaml_file = YamlFile("system-sa-dataplatform", "Data Platform Operator Service Account",
                                                    file_name, "system_dataplatform_components")
        self.yamls.append(system_sa_dataplatform_yaml_file)

        file_name = self.check_exists(self.system_dataplatform, "system-cr-dataplatform.yaml")
        system_cr_dataplatform_yaml_file = YamlFile("system-cr-dataplatform", "Data Platform Operator ClusterRole",
                                                    file_name, "system_dataplatform_components")
        self.yamls.append(system_cr_dataplatform_yaml_file)

        file_name = self.check_exists(self.system_dataplatform, "system-crb-dataplatform.yaml")
        system_crb_dataplatform_yaml_file = YamlFile("system-crb-dataplatform",
                                                     "Data Platform Operator ClusterRoleBinding", file_name,
                                                     "system_dataplatform_components")
        self.yamls.append(system_crb_dataplatform_yaml_file)

        file_name = self.check_exists(self.system_dataplatform, "system-crd-dataplatformoperator.yaml")
        system_crd_dataplatform_yaml_file = YamlFile("system-crd-dataplatform", "Data Platform CRD", file_name,
                                                     "system_dataplatform_components")
        self.yamls.append(system_crd_dataplatform_yaml_file)

        file_name = self.check_exists(self.system_dataplatform, "system-deploy-dataplatformoperator.yaml")
        system_dataplatformoperator_yaml_file = YamlFile("system-dataplatformoperator", "Data Platform Operator",
                                                         file_name, "system_dataplatform_components")
        self.yamls.append(system_dataplatformoperator_yaml_file)

        # file_name = self.check_exists(self.system_dataplatform, "system-scc-dataplatform.yaml")
        # system_scc_dataplatform_yaml_file = YamlFile("system-scc-dataplatform", "Data Platform Operator SCC" ,file_name, "system-dataplatform_components", True)
        # self.yamls.append(system_scc_dataplatform_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform_setup, "template-namespace.yaml")
        template_namespace_yaml_file = YamlFile("template-namespace", "Data Platform Templates Namespace", file_name,
                                                "dataplatform_templates")
        self.yamls.append(template_namespace_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-admincli-cm.yaml")
        template_admincli_cm_yaml_file = YamlFile("template-admincli-cm", "Data Platform Templates AdminCLI CM",
                                                  file_name, "dataplatform_templates")
        self.yamls.append(template_admincli_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-cldb-cm.yaml")
        template_cldb_cm_yaml_file = YamlFile("template-cldb-cm", "Data Platform Templates CLDB CM", file_name,
                                              "dataplatform_templates")
        self.yamls.append(template_cldb_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-collectd-cm.yaml")
        template_collectd_cm_yaml_file = YamlFile("template-collectd-cm", "Data Platform Templates Collectd CM",
                                                  file_name, "dataplatform_templates")
        self.yamls.append(template_collectd_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-elasticsearch-cm.yaml")
        template_elasticsearch_cm_yaml_file = YamlFile("template-elasticsearch-cm",
                                                       "Data Platform Templates Elastic Search CM", file_name,
                                                       "dataplatform_templates")
        self.yamls.append(template_elasticsearch_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-fluent-cm.yaml")
        template_fluent_cm_yaml_file = YamlFile("template-fluent-cm", "Data Platform Templates Fluent CM", file_name,
                                                "dataplatform_templates")
        self.yamls.append(template_fluent_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-httpfs-cm.yaml")
        template_httpfs_cm_yaml = YamlFile("template-httpfs-cm", "Data Platform Templates HTTPfs CM", file_name,
                                           "dataplatform_templates")
        self.yamls.append(template_httpfs_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-grafana-cm.yaml")
        template_grafana_cm_yaml = YamlFile("template-grafana-cm", "Data Platform Templates Grafana CM", file_name,
                                            "dataplatform_templates")
        self.yamls.append(template_grafana_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-kibana-cm.yaml")
        template_kibana_cm_yaml = YamlFile("template-kibana-cm", "Data Platform Templates Kibana CM", file_name,
                                           "dataplatform_templates")
        self.yamls.append(template_kibana_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-maprgateway-cm.yaml")
        template_maprgateway_cm_yaml = YamlFile("template-maprgateway-cm", "Data Platform Templates Mapr Gateway CM",
                                                file_name, "dataplatform_templates")
        self.yamls.append(template_maprgateway_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-mfs-cm.yaml")
        template_mfs_cm_yaml = YamlFile("template-mfs-cm", "Data Platform Templates MFS CM", file_name,
                                        "dataplatform_templates")
        self.yamls.append(template_mfs_cm_yaml)

        # file_name = self.check_exists(self.templates_dataplatform, "template-nfs-cm.yaml")
        # template_nfs_cm_yaml = YamlFile("template-nfs-cm", "Data Platform Templates NFS CM" ,file_name, "dataplatform_templates", True)
        # self.yamls.append(template_nfs_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-objectstore-cm.yaml")
        template_objectstore_cm_yaml = YamlFile("template-objectstore-cm", "Data Platform Templates Objectstore CM",
                                                file_name, "dataplatform_templates")
        self.yamls.append(template_objectstore_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-opentsdb-cm.yaml")
        template_opentsdb_cm_yaml = YamlFile("template-opentsdb-cm", "Data Platform Templates OpenTSDB CM", file_name,
                                             "dataplatform_templates")
        self.yamls.append(template_opentsdb_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-webserver-cm.yaml")
        template_webserver_cm_yaml = YamlFile("template-webserver-cm", "Data Platform Templates Webserver CM",
                                              file_name, "dataplatform_templates")
        self.yamls.append(template_webserver_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-zookeeper-cm.yaml")
        template_zookeeper_cm_yaml = YamlFile("template-zookeeper-cm", "Data Platform Templates Zookeeper CM",
                                              file_name, "dataplatform_templates")
        self.yamls.append(template_zookeeper_cm_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-role-dataplatform.yaml")
        template_role_dataplatform_yaml = YamlFile("template-role-dataplatform", "Data Platform Templates Role",
                                                   file_name, "dataplatform_templates")
        self.yamls.append(template_role_dataplatform_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-role-dataplatform-user.yaml")
        template_role_dataplatform_user_yaml = YamlFile("template-role-dataplatform-user",
                                                        "Data Platform Templates User Role", file_name,
                                                        "dataplatform_templates")
        self.yamls.append(template_role_dataplatform_user_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-role-admincli.yaml")
        template_role_admincli_yaml = YamlFile("template-role-admincli", "Data Platform AdminCLI Templates Role",
                                               file_name, "dataplatform_templates")
        self.yamls.append(template_role_admincli_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-clusterrole-metrics.yaml")
        template_clusterrole_metrics_yaml = YamlFile("template-clusterrole-metrics",
                                              "Data Platform Templates Cluster Role for metrics service account",
                                              file_name, "dataplatform_templates")
        self.yamls.append(template_clusterrole_metrics_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-clusterrole-init.yaml")
        template_clusterrole_init_yaml = YamlFile("template-clusterrole-init",
                                              "Data Platform Templates Cluster Role for init service account",
                                              file_name, "dataplatform_templates")
        self.yamls.append(template_clusterrole_init_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-clusterrole-noderw.yaml")
        template_clusterrole_noderw_yaml = YamlFile("template-clusterrole-noderw",
                                              "Data Platform Templates Cluster Role for node read/write ops",
                                              file_name, "dataplatform_templates")
        self.yamls.append(template_clusterrole_noderw_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-psp-dataplatform.yaml")
        template_psp_dataplatform_yaml = YamlFile("template-psp-dataplatform", "Data Platform Pod Security Policy",
                                                  file_name, "dataplatform_templates")
        self.yamls.append(template_psp_dataplatform_yaml)

        file_name = self.check_exists(self.templates_dataplatform, "template-kafkarest-cm.yaml")
        template_kafkarest_cm_yaml_file = YamlFile("template-kafkarest-cm", "Data Platform Templates Kafkarest CM",
                                                  file_name, "dataplatform_templates")
        self.yamls.append(template_kafkarest_cm_yaml_file)

        file_name = self.check_exists(self.templates_dataplatform, "template-hivemeta-cm.yaml")
        template_hivemeta_cm_yaml_file = YamlFile("template-hivemeta-cm", "Data Platform Templates Hive Metastore CM",
                                                  file_name, "dataplatform_templates")
        self.yamls.append(template_hivemeta_cm_yaml_file)

        return True

    def install_dataplatform(self, upgrade_mode=False, install_templates=False):
        installable_yaml_types = ["system_dataplatform_components"]
        if install_templates:
            installable_yaml_types.append("dataplatform_templates")
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_dataplatform(self, uninstall_templates=False):
        uninstallable_yaml_types = ["system_dataplatform_components"]
        if uninstall_templates:
            uninstallable_yaml_types.append("dataplatform_templates")
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
