import os
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.upgrade_strategy import Remove
from operations.upgrade_strategy import Apply
from operations.yamlfile import YamlFile


class SparkOld(OperationsBase):
    def __init__(self):
        super(SparkOld, self).__init__()
        self.spark_dir = os.path.abspath(os.path.join(self.prereq_dir, "spark"))
        if not os.path.exists(self.spark_dir):
            raise NotFoundException(self.spark_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.spark_dir, "spark-namespace-old.yaml")
        spark_namespace_yaml_file_old = YamlFile("spark-namespace-old", "Spark Namespace Old", file_name, "spark_components")
        self.yamls.append(spark_namespace_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-sa-old.yaml")
        spark_sa_yaml_file_old = YamlFile("spark-sa-old", "Spark Service Account Old", file_name, "spark_components")
        self.yamls.append(spark_sa_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-cr.yaml")
        spark_cr_yaml_file = YamlFile("spark-cr", "Spark Cluster Role", file_name, "spark_components")
        self.yamls.append(spark_cr_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-crb.yaml")
        spark_crb_yaml_file = YamlFile("spark-crb", "Spark Cluster Role Binding", file_name, "spark_components")
        self.yamls.append(spark_crb_yaml_file)

        file_name = self.check_exists(self.spark_dir, "spark-imagepullsecret-old.yaml")
        spark_imagepullsecret_yaml_file_old = YamlFile("spark-imagepullsecret-old", "secret to pull images for Spark Old", file_name, "spark_components")
        self.yamls.append(spark_imagepullsecret_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-crd-sparkapplication-old.yaml")
        spark_crd_sparkapplication_yaml_file_old = YamlFile("spark-crd-sparkapplication-old", "Spark Application CRD Old", file_name, "spark_components")
        self.yamls.append(spark_crd_sparkapplication_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-crd-sparkscheduledapplication-old.yaml")
        spark_crd_sparkscheduledapplication_yaml_file_old = YamlFile("spark-crd-sparkscheduledapplication-old", "Spark Scheduled Application CRD Old", file_name, "spark_components")
        self.yamls.append(spark_crd_sparkscheduledapplication_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-deploy-sparkoperator-old.yaml")
        spark_sparkoperator_yaml_file_old = YamlFile("spark-sparkoperator-old", "Spark Operator Old", file_name, "spark_components")
        self.yamls.append(spark_sparkoperator_yaml_file_old)
        self.custom_upgrade_strategies[spark_sparkoperator_yaml_file_old] = Remove(self)

        file_name = self.check_exists(self.spark_dir, "spark-svc-sparkoperator-old.yaml")
        spark_svc_sparkoperator_yaml_file_old = YamlFile("spark-svc-old", "Spark Operator Service Old", file_name, "spark_components")
        self.yamls.append(spark_svc_sparkoperator_yaml_file_old)

        file_name = self.check_exists(self.spark_dir, "spark-job-sparkoperator-old.yaml")
        spark_job_sparkoperator_yaml_file_old = YamlFile("spark-job-old", "Spark Operator Job Old", file_name, "spark_components", False)
        self.yamls.append(spark_job_sparkoperator_yaml_file_old)

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
