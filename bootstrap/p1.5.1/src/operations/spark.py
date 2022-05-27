import os
import re
import sys
from common.mapr_logger.log import Log
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from bootstrapbase import BootstrapBase
from operations.upgrade_strategy import RemoveAndCreate
from common.os_command import OSCommand

class Spark(OperationsBase):
    spark_chart = "sparkoperator"
    spark_components = [("Spark Operator Job", "Job", "sparkoperator-init"),
                        ("Spark Operator Service", "Service", "spark-webhook"),
                        ("Spark Operator", "Deployment", "sparkoperator"),
                        ("Spark Scheduled Application CRD", "CustomResourceDefinition",
                         "scheduledsparkapplications.sparkoperator.hpe.com"),
                        ("Spark Application CRD", "CustomResourceDefinition",
                         "sparkapplications.sparkoperator.hpe.com"),
                        ("secret to pull images for Spark", "Secret", "hpe-imagepull-secrets"),
                        ("Spark Cluster Role Binding", "ClusterRoleBinding", "hpe-sparkoperator"),
                        ("Spark Cluster Role", "ClusterRole", "hpe-sparkoperator"),
                        ("Spark Service Account", "ServiceAccount", "hpe-sparkoperator"),
                        ("Spark Namespace", "Namespace", "hpe-spark-operator")]

    def __init__(self):
        super(Spark, self).__init__()

    def uninstall_each_component(self):
        log_prefix_str = "Deleting "
        success_log_prefix_str = "Deleted "
        for component in self.spark_components:
            Log.info(os.linesep + log_prefix_str + component[0] + " ...", True)
            uninstall_command = "kubectl delete " + component[1] + " " + component[2] + " -n hpe-spark-operator"
            response, status = OSCommand.run2(uninstall_command)
            if status != 0:
                Log.error("Failed to uninstall " + component[0])
            Log.info(success_log_prefix_str + component[0] + ".")

    def uninstall_spark_components(self):
        self.uninstall_each_component()
