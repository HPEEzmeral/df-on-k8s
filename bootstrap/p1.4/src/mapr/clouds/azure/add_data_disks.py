from azure.mgmt.compute.models import DiskCreateOptionTypes
from azure.mgmt.compute.models import StorageAccountTypes

from common.mapr_logger.log import Log


class AddDataDisks(object):
    def __init__(self, env, compute_client):
        self.env = env
        self.compute_client = compute_client

        self.aks_rg = self.env.get("RESOURCE_GROUP")
        self.aks_name = self.env.get("AKS_NAME")
        self.location = self.env.get("LOCATION")
        self.data_disk_count = self.env.get_int("DATA_DISK_COUNT")
        self.data_disk_size = self.env.get_int("DATA_DISK_SIZE")
        self.data_disk_type = self.env.get("DATA_DISK_TYPE")

        self.resource_group = "MC_{0}_{1}_{2}".format(self.aks_rg, self.aks_name, self.location)

        if self.data_disk_type is None:
            Log.info("DATA_DISK_TYPE not supplied, using Standard_LRS", True)
            self.data_disk_type = StorageAccountTypes.standard_lrs
        elif (self.data_disk_type != "Standard_LRS") and \
             (self.data_disk_type != "StandardSSD_LRS") and \
             (self.data_disk_type != "Premium_LRS"):
            Log.info("Invalid disk type {0}, using Standard_LRS".format(self.data_disk_type), True)
            self.data_disk_type = StorageAccountTypes.standard_lrs
        else:
            Log.info("Creating data disks of type; {0}".format(self.data_disk_type), True)

    def run(self):
        Log.info("Checking disks in resource group: {0}...".format(self.resource_group), True)

        existing_disks = self.compute_client.disks.list_by_resource_group(self.resource_group)
        for disk in existing_disks:
            Log.info("Found managed disk: {0}".format(disk.name), True)

        vms = self.compute_client.virtual_machines.list(self.resource_group)
        for vm in vms:
            Log.info("Checking VM: {0} for data disks".format(vm.name), True)
            attached_disks = vm.storage_profile.data_disks
            Log.info("Found {0} data disk(s) attached to the VM".format(len(attached_disks)), True)

            if len(attached_disks) >= self.data_disk_count:
                Log.info("There are already {0} data disk(s) attached when only {1} were required".format(len(attached_disks),
                                                                                                          self.data_disk_count), True)
                continue

            disks = list()
            for i in range(len(attached_disks), self.data_disk_count):
                data_disk_name = "{0}_DataDisk_{1}".format(vm.name, i)
                Log.info("Creating or updating data disk: {0}...".format(data_disk_name), True)

                disk = self.create_disk(data_disk_name)
                disks.append(disk)
                Log.info("The data disk is: {0}".format(disk.name), True)

            Log.info("Attaching the data disks to the vm...", True)
            self.attach_disks(vm, disks, len(attached_disks))

    def create_disk(self, name):
        async_creation = self.compute_client.disks.create_or_update(
            self.resource_group,
            name,
            {
                'location': self.location,
                'disk_size_gb': self.data_disk_size,
                'creation_data': {
                    'create_option': DiskCreateOptionTypes.empty
                },
                'sku': {
                    'name': self.data_disk_type
                }
            }
        )
        disk_resource = async_creation.result()
        return disk_resource

    def attach_disks(self, vm, disks, lun):
        vm = self.compute_client.virtual_machines.get(
            self.resource_group,
            vm.name
        )

        for disk in disks:
            new_disk = {
                'lun': lun,
                'name': disk.name,
                'create_option': DiskCreateOptionTypes.attach,
                'managed_disk': {
                    'id': disk.id
                }
            }
            vm.storage_profile.data_disks.append(new_disk)
            lun += 1

        async_update = self.compute_client.virtual_machines.create_or_update(
            self.resource_group,
            vm.name,
            vm
        )
        async_update.wait()
