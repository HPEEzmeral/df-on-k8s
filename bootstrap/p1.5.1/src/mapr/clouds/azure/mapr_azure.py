import urllib

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.monitor import MonitorClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials, UserPassCredentials

from common.mapr_logger.log import Log
from mapr.clouds.azure.create_aks import CreateAKS
from common.mapr_exceptions.ex import AzureException


class MapRAzure(object):
    SERVICE_PRINCIPAL = "service_principal"
    USER_PASSWORD = "user_password"

    def __init__(self, context):
        self.context = context

        self.credentials = None
        self.resource_client = None
        self.compute_client = None
        self.network_client = None
        self.monitor_client = None

        self._validate_credentials()

    def _get_credentials(self):
        if self.context.auth_type == MapRAzure.SERVICE_PRINCIPAL:
            secret = urllib.quote(self.context.secret)
            credentials = ServicePrincipalCredentials(self.context.client_id, secret, tenant=self.context.tenant)
        else:
            credentials = UserPassCredentials(self.context.username, self.context.password, client_id=self.context.client_id)

        return credentials

    def _validate_credentials(self):
        if self.context.auth_type == MapRAzure.SERVICE_PRINCIPAL:
            if len(self.context.client_id) == 0:
                raise AzureException("client_id must be set when "
                                     "using service_principal auth type")
            if len(self.context.secret) == 0:
                raise AzureException("secret must be set when using "
                                     "service_principal auth type")
            if len(self.context.tenant) == 0:
                raise AzureException("tenant must be set when using "
                                     "service_principal auth type")
            if len(self.context.subscription_id) == 0:
                raise AzureException("subscription_id must be set when using "
                                     "service_principal auth type")
        elif self.context.auth_type == MapRAzure.USER_PASSWORD:
            if len(self.context.username) == 0:
                raise AzureException("username must be set when "
                                     "using user_password auth type")
            if len(self.context.password) == 0:
                raise AzureException("password must be set when "
                                     "using user_password auth type")
        else:
            raise AzureException("auth_type must be service_principal"
                                 " or user_password")

    def login(self):
        self.credentials = self._get_credentials()
        self.get_clients()

    def create_cluster(self):
        create_aks = CreateAKS(self.context, self.resource_client)
        create_aks.run()

    def get_clients(self):
        Log.info("Getting Azure clients...", True)
        self.resource_client = ResourceManagementClient(self.credentials, self.context.subscription_id)
        self.compute_client = ComputeManagementClient(self.credentials, self.context.subscription_id)
        self.network_client = NetworkManagementClient(self.credentials, self.context.subscription_id)
        self.monitor_client = MonitorClient(self.credentials, self.context.subscription_id)
