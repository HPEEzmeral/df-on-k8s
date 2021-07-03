from common.mapr_logger.log import Log


class AddPublicIp(object):
    def __init__(self, env, compute_client, network_client):
        self.env = env
        self.compute_client = compute_client
        self.network_client = network_client

        self.aks_rg = self.env.get("RESOURCE_GROUP")
        self.aks_name = self.env.get("AKS_NAME")
        self.location = self.env.get("LOCATION")

        self.resource_group = "MC_{0}_{1}_{2}".format(self.aks_rg, self.aks_name, self.location)

    def run(self):
        # vms = self.compute_client.virtual_machines.list(self.resource_group)
        # for vm in vms:
        #     nic = vm.network_profile.network_interfaces
        #     pass

        nics = self.network_client.network_interfaces.list(self.resource_group)
        for nic in nics:
            ipconfig = nic.ip_configurations[0]

            public_ip_name = "{0}-publicip".format(nic.name)
            public_ip = {
                'location': self.location,
                'public_ip_allocation_method': 'Dynamic'
            }

            if ipconfig.public_ip_address is not None:
                Log.info("{0} NIC already has a public ip address".format(nic.name), True)
                continue

            Log.info("Creating or updating public ip address {0}...".format(public_ip_name), True)
            ip_rslt = self.network_client.public_ip_addresses.create_or_update(self.resource_group, public_ip_name, public_ip)
            ip_rslt.wait()

            public_ip = self.network_client.public_ip_addresses.get(self.resource_group, public_ip_name)
            ipconfig.public_ip_address = public_ip

            params = {
                'location': self.location,
                'ip_configurations': [ipconfig]
            }

            Log.info("Associate public ip address {0} with NIC {1}".format(public_ip_name, nic.name), True)
            ip_rslt = self.network_client.network_interfaces.create_or_update(self.resource_group, nic.name, params)
            ip_rslt.wait()
