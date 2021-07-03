import json
import os

from azure.mgmt.resource.resources.models import ResourceGroup, DeploymentProperties, DeploymentMode

from common.mapr_logger.log import Log
from common.os_command import OSCommand


class CreateAKS(object):
    ARM_TEMPLATE_JSON = "../../../conf/azure/aks-arm-template.json"
    PARAMETERS_JSON = "../../../conf/azure/aks-arm-parameters.json"

    def __init__(self, context, resource_client):
        self.context = context
        self.resource_client = resource_client
        self.base_path = os.path.dirname(__file__)

    def _create_update_resource_group(self):
        Log.info("Creating or updating resource group: {0}...".format(self.context.resource_group), True)
        resource = ResourceGroup(location=self.context.location)
        self.resource_client.resource_groups.create_or_update(self.context.resource_group, resource)

    def _create_aks(self):
        with open(os.path.join(self.base_path, CreateAKS.PARAMETERS_JSON)) as in_file:
            parameters = json.load(in_file)

        parameters[u"resourceName"][u"value"] = self.context.aks_name
        parameters[u"agentCount"][u"value"] = self.context.node_count
        parameters[u"agentVMSize"][u'Value'] = self.context.vm_size
        parameters[u"osDiskSizeGB"][u'Value'] = int(self.context.os_disk_size)
        parameters[u"sshRSAPublicKey"][u'Value'] = self.context.public_key
        parameters[u"servicePrincipalClientId"][u'Value'] = self.context.client_id
        parameters[u"servicePrincipalClientSecret"][u'Value'] = self.context.secret
        parameters[u"kubernetesVersion"][u'Value'] = self.context.k8s_version
        parameters[u"dnsPrefix"][u'Value'] = "{0}-maprtech".format(self.context.aks_name)

        with open(os.path.join(self.base_path, CreateAKS.ARM_TEMPLATE_JSON)) as in_file:
            template = json.load(in_file)

        deployment_properties = DeploymentProperties()
        deployment_properties.template = template
        deployment_properties.parameters = parameters
        deployment_properties.mode = DeploymentMode.incremental

        Log.info("{0}: Run K8S deployment test with {1} Nodes OS Disk Size {2}...".format(self.context.resource_group, self.context.node_count, self.context.os_disk_size), True)
        deployment_async_operation = self.resource_client.deployments.create_or_update(self.context.resource_group,
                                                                                       "maprk8s.deployment", deployment_properties)
        deployment_async_operation.wait()
        Log.info("K8S cluster deployment complete", True)

    def run(self):
        self._create_update_resource_group()
        self._create_aks()

        # cmd = "az aks get-credentials --resource-group {0} --name {1}".format(self.context.resource_group, self.context.aks_name)
        # rslt, status = OSCommand.run2(cmd)
        # Log.info("Get credentials results: {0}: {1}".format(status, rslt))
