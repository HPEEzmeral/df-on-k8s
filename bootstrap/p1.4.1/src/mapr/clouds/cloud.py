import imp
import inspect
import os
import sys

from common.environment import Environment
from common.mapr_logger.log import Log
from common.mapr_exceptions.ex import NotImplementedException, NotFoundException


class Cloud(object):
    DIR = os.path.dirname(__file__)
    CLOUD_USER = "user@mycompany.com"
    CLUSTER_NAME = "{0}-cluster"
    PROJECT_NAME = "myproject"
    
    _clouds = None
    _cloud_instances = None
    prompts = None

    def __init__(self):
        self.enabled = None
        self.available = None
        self._is_core_usage = False

        self.env = Environment(sys.argv)
        self.cluster_name = Cloud.CLUSTER_NAME.format(self.env.get("USER"))

    # The name of the cloud module
    def get_name(self):
        raise NotImplementedException("get_name method must be implemented")

    # any operations that are needed to build the cloud K8S cluster are done here
    def build_cloud(self):
        raise NotImplementedException("build_cloud method must be implemented")

    # after the cloud is built, any configuration of K8S client is done here
    def configure_cloud(self):
        raise NotImplementedException("configure_cloud method must be implemented")

    # is this cloud enabled and should be seen by the end user (immediete fast checks)
    def is_enabled(self):
        raise NotImplementedException("is_enabled method must be implemented")

    # if the cloud is available after determining that the particular cloud is enabled (long running checks)
    def is_available(self):
        raise NotImplementedException("is_available method must be implemented")

    # Get a list of cloud usages, display them to the user and set the one choosen
    def setup_cloud_usage(self):
        raise NotImplementedException("setup_cloud_usage method must be implemented")

    @staticmethod
    def initialize(prompts):
        Cloud.prompts = prompts
        Cloud._clouds = list()
        Cloud._cloud_instances = dict()
        files = os.listdir(Cloud.DIR)

        Log.info("Initializing cloud support. One moment please...")

        for afile in files:
            full_file = os.path.join(Cloud.DIR, afile)
            if not full_file.endswith(".py"):
                Log.debug("Not inspecting: {0} because it is not a py file".format(full_file))
                continue
            if not os.path.isfile(full_file):
                Log.debug("Not inspecting: {0} because it is not a file".format(full_file))
                continue
            if afile == "cloud.py" or afile == "__init__.py":
                Log.debug("Not inspecting: {0} because it is not a file".format(full_file))
                continue

            module_name = full_file[:full_file.index(".")]
            file_module = imp.load_source(module_name, os.path.join(Cloud.DIR, full_file))
            class_members = inspect.getmembers(file_module, inspect.isclass)
            Log.debug("class_members for file_module {0} is: {1}".format(str(file_module), str(class_members)))

            for clazz in class_members:
                # if the class is of the correct subclass add it to the list of tests
                if not issubclass(clazz[1], Cloud) or clazz[1] == Cloud or clazz[1] in Cloud._clouds:
                    continue

                Cloud._clouds.append(clazz[1])
                instance = clazz[1]()
                name = instance.get_name()
                if instance.is_enabled():
                    Cloud._cloud_instances[name] = instance
                    Log.debug("Cloud {0} was added to list because it is enabled".format(name))
                else:
                    Log.debug("Cloud {0} was not added to list because it is not enabled".format(name))

        Log.debug("There were {0} cloud providers found".format(len(Cloud._clouds)))

    @staticmethod
    def check_available():
        available_instances = dict()
        for cloud_name, cloud_instance in Cloud._cloud_instances.items():
            if cloud_instance.is_available():
                Log.debug("{0} cloud is available".format(cloud_name))
                available_instances[cloud_name] = cloud_instance
            else:
                Log.warning("{0} cloud was enabled but did not pass availability tests".format(cloud_name))

        Cloud._cloud_instances = available_instances

    @staticmethod
    def get_instance(name):
        instance = Cloud._cloud_instances.get(name)
        if instance is None:
            raise NotFoundException("Could not find an instance with a name of {0}".format(name))
        return instance

    @staticmethod
    def get_cloud_names():
        return sorted(Cloud._cloud_instances.keys())
