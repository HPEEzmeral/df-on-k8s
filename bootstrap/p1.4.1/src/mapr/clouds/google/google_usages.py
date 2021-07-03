from common.mapr_exceptions.ex import NotFoundException


class GoogleUsages(object):
    USAGE_BASE = {
        "Zone": "us-central1-a",
        "ImageType": "COS",
        "DiskTypeOnNode": "pd-ssd",
        "K8SVersion": "latest",
        "K8SAlphaVersion": "1.13.4-gke.10"
    }
    USAGE_COMPUTE_NAME = "Compute Only"
    USAGE_COMPUTE = {
        "Name": USAGE_COMPUTE_NAME,
        "OSDiskSize": 200,
        "BlockDiskSize": 16,
        "Nodes": 2,
        "Disks": 1,
        "InstanceType": "n1-standard-8"
    }
    USAGE_CORE_COMPUTE_NAME = "Extreme Core and Compute"
    USAGE_CORE_COMPUTE = {
        "Name": USAGE_CORE_COMPUTE_NAME,
        "OSDiskSize": 500,
        "BlockDiskSize": 128,
        "Nodes": 5,
        "Disks": 3,
        "InstanceType": "n1-standard-32"
    }
    USAGE_SMALL_CORE_COMPUTE_NAME = "Small Core and Compute"
    USAGE_SMALL_CORE_COMPUTE = {
        "Name": USAGE_SMALL_CORE_COMPUTE_NAME,
        "OSDiskSize": 400,
        "BlockDiskSize": 128,
        "Nodes": 3,
        "Disks": 1,
        "InstanceType": "n1-standard-16"
    }

    # Add the base dictonary with common options to the usages
    USAGE_COMPUTE.update(USAGE_BASE)
    USAGE_CORE_COMPUTE.update(USAGE_BASE)
    USAGE_SMALL_CORE_COMPUTE.update(USAGE_BASE)

    # This is the list of usages
    USAGES = [USAGE_COMPUTE, USAGE_SMALL_CORE_COMPUTE, USAGE_CORE_COMPUTE]

    @staticmethod
    def get_values_in_usages(key):
        return [sub[key] for sub in GoogleUsages.USAGES]

    @staticmethod
    def get_usage_names():
        names = GoogleUsages.get_values_in_usages("Name")
        return names

    @staticmethod
    def get_usage_from_name(usage_name):
        all_names = GoogleUsages.get_usage_names()

        if usage_name not in all_names:
            raise NotFoundException("Cannot find Usage name {0} in list of names {1}".format(usage_name, str(all_names)))

        usage = None
        for this_usage in GoogleUsages.USAGES:
            if this_usage["Name"] == usage_name:
                usage = this_usage
                break

        return usage

    def __init__(self, usage_name):
        self.usage = GoogleUsages.get_usage_from_name(usage_name)

    def get(self, key):
        if self.usage is None:
            raise NotFoundException("There is no set usage")

        value = self.usage.get(key)
        if value is None:
            raise NotFoundException("Could not find key '{0}' in dictonary {1}".format(key, str(self.usage)))

        return value
