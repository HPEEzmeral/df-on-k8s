import os
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.upgrade_strategy import RemoveAndCreate
from operations.yamlfile import YamlFile


class Spark(OperationsBase):
    def __init__(self):
        super(Spark, self).__init__()
        self.spark_dir = os.path.abspath(os.path.join(self.prereq_dir, "spark"))
        if not os.path.exists(self.spark_dir):
            raise NotFoundException(self.spark_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.spark_dir, "spark-namespace.yaml")
        spark_namespace_yaml_file = YamlFile("spark-namespace", "Spark Namespace", file_name, "spark_components")
        self.yamls.append(spark_namespace_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-sa.yaml")
        spark_sa_yaml_file = YamlFile("spark-sa", "Spark Service Account", file_name, "spark_components")
        self.yamls.append(spark_sa_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-cr.yaml")
        spark_cr_yaml_file = YamlFile("spark-cr", "Spark Cluster Role", file_name, "spark_components")
        self.yamls.append(spark_cr_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-crb.yaml")
        spark_crb_yaml_file = YamlFile("spark-crb", "Spark Cluster Role Binding", file_name, "spark_components")
        self.yamls.append(spark_crb_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-imagepullsecret.yaml")
        spark_imagepullsecret_yaml_file = YamlFile("spark-imagepullsecret", "secret to pull images for Spark", file_name, "spark_components")
        self.yamls.append(spark_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-crd-sparkapplication.yaml")
        spark_crd_sparkapplication_yaml_file = YamlFile("spark-crd-sparkapplication", "Spark Application CRD", file_name, "spark_components")
        self.yamls.append(spark_crd_sparkapplication_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-crd-sparkscheduledapplication.yaml")
        spark_crd_sparkscheduledapplication_yaml_file = YamlFile("spark-crd-sparkscheduledapplication", "Spark Scheduled Application CRD", file_name, "spark_components")
        self.yamls.append(spark_crd_sparkscheduledapplication_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-deploy-sparkoperator.yaml")
        spark_sparkoperator_yaml_file = YamlFile("spark-sparkoperator", "Spark Operator", file_name, "spark_components")
        self.yamls.append(spark_sparkoperator_yaml_file)
        self.custom_upgrade_strategies[spark_sparkoperator_yaml_file] = RemoveAndCreate(self)

        file_name = self.check_exists(self.spark_dir, "spark-svc-sparkoperator.yaml")
        spark_svc_sparkoperator_yaml_file = YamlFile("spark-svc", "Spark Operator Service", file_name, "spark_components")
        self.yamls.append(spark_svc_sparkoperator_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-job-sparkoperator.yaml")
        spark_job_sparkoperator_yaml_file = YamlFile("spark-job", "Spark Operator Job", file_name, "spark_components", False)
        self.yamls.append(spark_job_sparkoperator_yaml_file)

        # file_name = self.check_exists(self.spark_dir, "spark-scc.yaml")
        # spark_scc_yaml_file = YamlFile("spark-scc", "SCC",file_name, "spark_components", True)
        # self.yamls.append(spark_scc_yaml_file)

        return True

    def install_spark_components(self, upgrade_mode=False):
        installable_yaml_types = ["spark_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_spark_components(self):
        uninstallable_yaml_types = ["spark_components"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
