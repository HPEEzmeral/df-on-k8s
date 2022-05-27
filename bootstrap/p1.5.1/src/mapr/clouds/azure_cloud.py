import time

from bootstrapbase import BootstrapBase
from common.mapr_logger.log import Log
from common.os_command import OSCommand
from mapr.clouds.azure.aks_context import AKSContext
from mapr.clouds.cloud import Cloud


class AzureCloud(Cloud):
    NAME = "Azure"

    def __init__(self):
        super(AzureCloud, self).__init__()
        self.context = AKSContext()

        self.context.node_count = 3
        self.context.location = "centralus"
        self.context.vm_size = "Standard_D32s_v3"
        self.context.k8s_version = "1.12.6"

    def get_name(self):
        return AzureCloud.NAME

    def is_enabled(self):
        self.enabled = False
        return self.enabled

    def is_available(self):
        if not self.enabled:
            return False

        if self.available is None:
            Log.info("Checking Azure cloud availability. One moment...", True)

            if self.available is None:
                try:
                    from mapr.clouds.azure.mapr_azure import MapRAzure
                    from mapr.clouds.azure.create_aks import CreateAKS
                    from mapr.clouds.azure.add_data_disks import AddDataDisks
                    from mapr.clouds.azure.add_public_ip import AddPublicIp
                    self.available = True
                except ImportError as ie:
                    Log.error("Azure verification error: {0}".format(str(ie)))
                    self.available = False

        return self.available

    def build_cloud(self):
        from mapr.clouds.azure.mapr_azure import MapRAzure

        # self.context.auth_type = MapRAzure.USER_PASSWORD
        self.context.auth_type = MapRAzure.SERVICE_PRINCIPAL
        self.context.username = self.prompts.prompt("Azure login user name", key_name="AZURE_USERNAME")
        self.context.password = self.prompts.prompt("Azure login password", password=True, key_name="AZURE_PASSWORD")
        self.context.subscription_id = self.prompts.prompt("Azure subscription id", key_name="AZURE_SUBSCRIPTION")
        self.context.tenant = self.prompts.prompt("Azure tenant", key_name="AZURE_TENANT")
        self.context.client_id = self.prompts.prompt("Azure client id", key_name="AZURE_CLIENT_ID")
        self.context.secret = self.prompts.prompt("Azure secret", password=True, key_name="AZURE_SECRET")

        self.context.location = self.prompts.prompt("Azure location(region)", self.context.location, key_name="AZURE_LOCATION")
        self.context.resource_group = self.prompts.prompt("Azure resource group name", key_name="AZURE_RESOURCE_GROUP_NAME")
        self.context.aks_name = self.prompts.prompt("Azure AKS cluster name", key_name="AZURE_AKS_CLUSTER_NAME")
        self.context.node_count = self.prompts.prompt_integer("Azure AKS node count", self.context.node_count, 1, key_name="AZURE_AKS_NODE_COUNT")
        self.context.vm_size = self.prompts.prompt("Azure virtual machine size", self.context.vm_size, key_name="AZURE_VM_SIZE")
        self.context.k8s_version = self.prompts.prompt("Kubernetes version", self.context.k8s_version, key_name="AZURE_K8S_VERSION")
        self.context.public_key = self.prompts.prompt("Azure nodes public key", key_name="AZURE_PUBLIC_KEY")
        self.context.os_disk_size = 127

        if not self.prompts.prompt_boolean("Ready to create Azure AKS cluster. Do you want to continue?", True, key_name="AZURE_CREATE_AKS"):
            Log.error("Exiiting since user is not ready to continue")
            BootstrapBase.exit_application(100)

        Log.info("Logging into Azure...", True)
        azure = MapRAzure(self.context)
        azure.login()

        Log.info("Creating AKS cluster in Azure...", True)
        before = time.time()
        azure.create_cluster()
        after = time.time()
        diff = int(after - before)
        Log.info("Cluster creation took {0}m {1}s".format(diff / 60, diff % 60), True)

        Log.info("We need to log into Azure using the Azure CLI...")
        rslt, status = OSCommand.run2("az login -u {0} -p {1}".format(self.context.username, self.context.password))
        if status != 0:
            Log.error("Could not log into Azure: {0}:{1}", status, rslt)
        Log.info("Logged into Azure", True)

        Log.info("Now we will configure Kubectl for your kubernetes env...")
        rslt, status = OSCommand.run2("az aks get-credentials --resource-group {0} --name {1}".format(self.context.resource_group, self.context.aks_name))
        if status != 0:
            Log.error("Could not configure Kubectl for your kubernetes env: {0}:{1}", status, rslt)
        Log.info("Configured Kubectl", True)

    def configure_cloud(self):
        Log.debug("Nothing to do yet...")
