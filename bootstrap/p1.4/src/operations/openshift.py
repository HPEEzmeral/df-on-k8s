from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase


class OpenShift(OperationsBase):
    def __init__(self):
        super(OpenShift, self).__init__()

    def switch_to_oc(self):
        self.is_openshift = True

    def is_openshift_connected(self):
        """
        This command runs the `oc status` and return if Openshift is connected
        :return: True/False
        """

        cmd = "oc status"
        response = self._run_and_return_response(cmd, False)
        if response is None:
            return False
        elif "warnings" in response.lower():
            return False

        return True

    def run_oc_apply(self, key):
        yaml_file, changed = self.get_yaml(key)
        if yaml_file is None:
            raise NotFoundException("The key '{0}' does not have an entry in the yamls dictionary".format(key))

        cmd = "{0} {1}".format(OperationsBase.OC_APPLY, yaml_file)
        result = self._run(cmd)
        if changed:
            self.delete_temp_yaml(yaml_file)

        return result

    def run_oc_delete(self, key):
        yaml_file, changed = self.get_yaml(key)
        if yaml_file is None:
            raise NotFoundException("The key '{0}' does not have an entry in the yamls dictionary".format(key))

        cmd = "{0} {1}".format(OperationsBase.OC_DELETE, yaml_file)
        result = self._run(cmd)
        if changed:
            self.delete_temp_yaml(yaml_file)

        return result

    def nodesvc_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-nodesvc ' \
              ' system:serviceaccount:hpe-nodesvc:hpe-nodesvc'
        self._run(cmd)

    def nodesvc_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-nodesvc ' \
              ' system:serviceaccount:hpe-nodesvc:hpe-nodesvc'
        self._run(cmd)

    def csi_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-csi-nodeplugin ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-nodeplugin'
        self._run(cmd)

        cmd = 'oc adm policy add-cluster-role-to-user hpe-csi-attacher ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-provisioner'
        self._run(cmd)

        cmd = 'oc adm policy add-cluster-role-to-user hpe-csi-provisioner ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-provisioner'
        self._run(cmd)

    def csi_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-csi-nodeplugin ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-nodeplugin'
        self._run(cmd)

        cmd = 'oc adm policy remove-cluster-role-from-user hpe-csi-attacher ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-provisioner'
        self._run(cmd)

        cmd = 'oc adm policy remove-cluster-role-from-user hpe-csi-provisioner ' \
              ' system:serviceaccount:hpe-csi:hpe-csi-provisioner'
        self._run(cmd)

    def drill_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-drilloperator ' \
              ' system:serviceaccount:drill-operator:hpe-drilloperator'
        self._run(cmd)

    def drill_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-drilloperator ' \
              ' system:serviceaccount:drill-operator:hpe-drilloperator'
        self._run(cmd)

    def ingress_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-ingress ' \
              ' system:serviceaccount:hpe-ingress:hpe-ingress'
        self._run(cmd)

    def ingress_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-ingress ' \
              ' system:serviceaccount:hpe-ingress:hpe-ingress'
        self._run(cmd)

    def spark_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-sparkoperator ' \
              ' system:serviceaccount:spark-operator:hpe-sparkoperator'
        self._run(cmd)

    def spark_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-sparkoperator ' \
              ' system:serviceaccount:spark-operator:hpe-sparkoperator'
        self._run(cmd)

    def dataplatform_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-dataplatformoperator ' \
              ' system:serviceaccount:hpe-system:hpe-dataplatformoperator'
        self._run(cmd)

    def dataplatform_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-dataplatformoperator ' \
              ' system:serviceaccount:hpe-system:hpe-dataplatformoperator'
        self._run(cmd)

    def tenant_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-tenantoperator ' \
              ' system:serviceaccount:hpe-system:hpe-tenantoperator'
        self._run(cmd)

    def tenant_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-tenantoperator ' \
              ' system:serviceaccount:hpe-system:hpe-tenantoperator'
        self._run(cmd)

    def ui_openshift_policy_add(self):
        cmd = 'oc adm policy add-cluster-role-to-user hpe-maprui ' \
              ' system:serviceaccount:hpe-ui:hpe-maprui'
        self._run(cmd)

    def ui_openshift_policy_remove(self):
        cmd = 'oc adm policy remove-cluster-role-from-user hpe-maprui ' \
              ' system:serviceaccount:hpe-ui:hpe-maprui'
        self._run(cmd)
