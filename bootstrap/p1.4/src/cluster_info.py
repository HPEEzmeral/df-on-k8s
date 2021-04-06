import json
import os
import sys
import time

from common.mapr_exceptions.ex import MapRException
from common.mapr_logger.log import Log
from common.os_command import OSCommand


class ClusterInfo(object):
    SYSTEM = "hpe-system"
    SPARK = "hpe-spark-operator"
    SPARK_OLD = "spark-operator"
    LDAP = "hpe-ldap"
    CSI = "hpe-csi"
    ECP = "hpecp"
    ECP_53 = "falco"
    MAPR_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + SYSTEM + "\")]}'"
    SPARK_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + SPARK + "\")]}'"
    SPARK_EXISTS_OLD = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + SPARK_OLD + "\")]}'"
    LDAP_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + LDAP + "\")]}'"
    CSI_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + CSI + "\")]}'"
    ECP_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + ECP + "\")]}'"
    ECP_53_EXISTS = "kubectl get ns -o jsonpath='{.items[?(@.metadata.name == \"" + ECP_53 + "\")]}'"
    CLUSTER_INFO = "kubectl get pods -n {0} -o json -l \"app={1}\""
    LDAP_INFO = "kubectl get pods -n {0} -o json -l \"hpe.com/component={1}\""
    SPARK_INFO = "kubectl get pods -n " + SPARK + " -o json -l \"app.kubernetes.io/name=sparkoperator\""
    SPARK_INFO_OLD = "kubectl get pods -n " + SPARK_OLD + " -o json -l \"app.kubernetes.io/name=sparkoperator\""
    SPARK_OLD_RUNNING_POD = "kubectl get pods --no-headers -o custom-columns=\":metadata.name\" --field-selector=status.phase=Running -n " + SPARK_OLD + " | head -n 1 | tr -d '\n'"

    def __init__(self):
        self._system_namespace_exists = None
        self._spark_namespace_exists = None
        self._spark_namespace_exists_old = None
        self._ldap_namespace_exists = None
        self._csi_namespace_exists = None
        self._ecp_namespace_exists = None
        self._ecp_53_exists = None
        self._cluster_op_json = None
        self._tenant_op_json = None
        self._spark_op_json = None
        self._spark_op_json_old = None
        self._ldap_op_json = None
        self._csi_op_json = None

    def examine_cluster(self, wait_for_running):
        print("")
        Log.info("Gathering Data Fabric cluster information...", stdout=True)
        Log.info("Checking namespaces...", stdout=True)

        response, status = OSCommand.run2(ClusterInfo.MAPR_EXISTS)
        self._system_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._system_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.SYSTEM))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.SYSTEM))

        response, status = OSCommand.run2(ClusterInfo.SPARK_EXISTS)
        self._spark_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._spark_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.SPARK))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.SPARK))

        response, status = OSCommand.run2(ClusterInfo.SPARK_EXISTS_OLD)
        self._spark_namespace_exists_old = True if status == 0 and response != "<no response>" else False
        if not self._spark_namespace_exists_old:
            Log.info("The " + ClusterInfo.SPARK_OLD + " namespace was not found on this Kubernetes cluster")

        response, status = OSCommand.run2(ClusterInfo.LDAP_EXISTS)
        self._ldap_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._ldap_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.LDAP))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.LDAP))

        response, status = OSCommand.run2(ClusterInfo.CSI_EXISTS)
        self._csi_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._csi_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.CSI))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.CSI))

        response, status = OSCommand.run2(ClusterInfo.ECP_EXISTS)
        self._ecp_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._ecp_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.ECP))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.ECP))

        Log.info("Checking operators...", stdout=True)
        try:
            if self._system_namespace_exists:
                self._cluster_op_json = self.check_operator(wait_for_running, ClusterInfo.CLUSTER_INFO.format(ClusterInfo.SYSTEM, "dataplatformoperator"), "dataplatformoperator")

            if self._system_namespace_exists:
                self._tenant_op_json = self.check_operator(wait_for_running, ClusterInfo.CLUSTER_INFO.format(ClusterInfo.SYSTEM, "tenantoperator"), "tenantoperator")

            if self._spark_namespace_exists:
                self._spark_op_json = self.check_operator(wait_for_running, ClusterInfo.SPARK_INFO, "sparkoperator")

            if self._spark_namespace_exists_old:
                self._spark_op_json_old = self.check_operator(wait_for_running, ClusterInfo.SPARK_INFO_OLD, "sparkoperator")

            if self._ldap_namespace_exists:
                self._ldap_op_json = self.check_operator(wait_for_running, ClusterInfo.LDAP_INFO.format(ClusterInfo.LDAP, "ldap"), "ldap")

            if self._csi_namespace_exists:
                self._csi_op_json = self.check_operator(wait_for_running, ClusterInfo.CLUSTER_INFO.format(ClusterInfo.CSI, "hpe-controller-kdf"), "hpe-controller-kdf")
        except MapRException as me:
            Log.error(me.value)
            Log.info("Correct the above error and make sure that all pods are in a running state and try the operation again", stdout=True)
            sys.exit(1)

    @staticmethod
    def check_operator(wait_for_running, cmd, pod_name):
        json_val = None

        for i in range(1, 20):
            response, status = OSCommand.run2(cmd, truncate_response=200)
            if status != 0:
                Log.info("Could not gather {0} operator information".format(pod_name))
                continue

            json_val = ClusterInfo.get_json(response)
            status = json_val["items"][0]["status"]["phase"].lower()
            if not wait_for_running:
                if status != "running":
                    raise MapRException("The {0} pod is in a {1} state; Expected running".format(pod_name, status))
                break
            if status == "running":
                break

            Log.info("Waiting for the {0} operator to become running (was {1})...".format(pod_name, status), stdout=True)
            time.sleep(10)
            json_val = None

        if json_val is None:
            Log.warn("The {0} pod did not transition to a running state. The pod might still become running after waiting some more time".format(pod_name))
        return json_val

    @staticmethod
    def get_json(json_str):
        j = json.loads(json_str)
        if j is None or len(j.get("items")) == 0:
            return None
        return j

    def get_cluster_operator_json(self):
        return self._cluster_op_json

    def get_tenant_operator_json(self):
        return self._tenant_op_json

    def get_spark_operator_json(self):
        return self._spark_op_json

    def get_spark_operator_json_old(self):
        return self._spark_op_json_old

    def get_ldap_operator_json(self):
        return self._ldap_op_json

    def is_data_fabric_installed(self):
        return self._system_namespace_exists and self._cluster_op_json is not None

    def is_compute_installed(self):
        return self._system_namespace_exists and self._tenant_op_json is not None

    def is_ldap_installed(self):
        return self._ldap_namespace_exists and self._ldap_op_json is not None

    def is_spark_installed(self):
        return self._spark_namespace_exists and self._spark_op_json is not None

    def is_spark_installed_old(self):
        return self._spark_namespace_exists_old and self._spark_op_json_old is not None

    def is_csi_installed(self):
        return self._csi_namespace_exists and self._csi_op_json is not None

    def is_spark_old_ns_exists(self):
        return self._spark_namespace_exists_old

    def is_hpe_spark_in_old_ns(self):
        response_pod_name, status_pod_name = OSCommand.run2(ClusterInfo.SPARK_OLD_RUNNING_POD)
        response_hpe_spark_installed, status_hpe_spark_installed = OSCommand.run2("kubectl exec " + response_pod_name + " -n " + ClusterInfo.SPARK_OLD + " -- ls -la /opt/mapr/spark/sparkversion")
        return status_hpe_spark_installed == 0

    def is_ecp53(self):
        response, status = OSCommand.run2(ClusterInfo.ECP_EXISTS)
        self._ecp_namespace_exists = True if status == 0 and response != "<no response>" else False
        if not self._ecp_namespace_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.ECP))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.ECP))
        response, status = OSCommand.run2(ClusterInfo.ECP_53_EXISTS)
        self._ecp_53_exists = True if status == 0 and response != "<no response>" else False
        if not self._ecp_53_exists:
            Log.info("The {0} namespace was not found on this Kubernetes cluster".format(ClusterInfo.ECP_53))
        else:
            Log.info("The {0} namespace was found on this Kubernetes cluster".format(ClusterInfo.ECP_53))
        return self._ecp_namespace_exists and self._ecp_53_exists

    @staticmethod
    def _get_pod_info(json_obj, title):
        index = 0

        if json_obj is None:
            return ""
        items = json_obj.get("items")
        if items is None or len(items) == 0:
            Log.info("Pod JSON has no items")
        pod_name = json_obj["items"][index]["metadata"]["name"]
        create_time = json_obj["items"][index]["metadata"]["creationTimestamp"]
        image_name = json_obj["items"][index]["spec"]["containers"][0]["image"]
        image_name = image_name[image_name.rindex("/") + 1:]
        status = json_obj["items"][index]["status"]["phase"]
        return title + os.linesep + \
            "  Pod: {0}".format(pod_name) + os.linesep + \
            "  Image: {0}".format(image_name) + os.linesep + \
            "  Create Time: {0}".format(create_time) + os.linesep + \
            "  Status: {0}".format(status)

    def __str__(self):
        rslt = os.linesep + "data fabric installed: " + str(self.is_data_fabric_installed())
        rslt += os.linesep + "compute installed: " + str(self.is_compute_installed())
        rslt += os.linesep + "ldap installed: " + str(self.is_ldap_installed())
        rslt += os.linesep + "spark installed: " + str(self.is_spark_installed())
        rslt += os.linesep + "spark old installed: " + str(self.is_spark_installed_old())
        rslt += os.linesep + "csi installed: " + str(self.is_csi_installed())
        if self.is_data_fabric_installed():
            rslt += os.linesep + ClusterInfo._get_pod_info(self._cluster_op_json, "Data Platform Operator:")
        if self.is_compute_installed():
            rslt += os.linesep + ClusterInfo._get_pod_info(self._tenant_op_json, "Tenant Operator:")
        if self.is_ldap_installed():
            rslt += os.linesep + ClusterInfo._get_pod_info(self._ldap_op_json, "LDAP Pod:")
        if self._spark_op_json is not None:
            for i in range(0, len(self._spark_op_json["items"])):
                if self._spark_op_json["items"][i]["metadata"]["generateName"].find("sparkoperator-init-") == -1:
                    rslt += os.linesep + ClusterInfo._get_pod_info(self._spark_op_json, "Spark Operator:")
                    break

        return rslt
