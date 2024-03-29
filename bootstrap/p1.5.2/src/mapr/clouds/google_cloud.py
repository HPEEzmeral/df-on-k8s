import time
from threading import Thread

from bootstrapbase import BootstrapBase
from common.mapr_logger.log import Log
from common.os_command import OSCommand
from mapr.clouds.cloud import Cloud
from mapr.clouds.google.google_usages import GoogleUsages
from distutils.version import LooseVersion
import re
import yaml
import os


class GoogleCloud(Cloud):
    NAME = "Google"
    CMD_ROLE_BINDING = "kubectl create clusterrolebinding user-cluster-admin-binding --clusterrole=cluster-admin --user={0}"
    SUPPORTED_VERSIONS_FILE = "google/edf_gke_versions.yaml"
    GKE_RELEASE_CHANNELS = ["rapid", "regular", "stable"]

    def __init__(self):
        super(GoogleCloud, self).__init__()
        self._usage = None
        self.user = self.env.get("GCE_USER", GoogleCloud.CLOUD_USER)
        self.project = self.env.get("GKE_PROJECT_ID", GoogleCloud.PROJECT_NAME)
        self.zone = None
        self.image_type = None
        self.disk_type_on_node = None
        self.block_disk_size = None
        self.os_disk_size = None
        self.k8s_version = None
        self.alpha = False
        self.k8s_alpha_version = None
        self.k8s_edf_versions = None
        self.nodes = None
        self.disks = None
        self.instance_type = None
        self.channel = None
        self.enabled = True
        self.gke_channel_support = False
        self.supported_versions_file = os.path.join(Cloud.DIR, GoogleCloud.SUPPORTED_VERSIONS_FILE)
        self.edf_supported_versions = None

    def validate_versions_file(self):
        if not os.path.exists(self.supported_versions_file):
            Log.error("Supported Versions File {0} missing. Refer to example_edf_gke_versions.yaml"
                      " file under ./src/mapr/clouds/google/".format(self.supported_versions_file))
            BootstrapBase.exit_application(97)
        if os.stat(self.supported_versions_file).st_size == 0:
            Log.error("Supported Versions File {0} is empty".format(self.supported_versions_file))
            BootstrapBase.exit_application(98)
        with open(self.supported_versions_file) as fp:
            try:
                self.k8s_edf_versions = yaml.safe_load(fp) or {}
            except Exception as e:
                raise e
        if self.k8s_edf_versions is None:
            Log.error("Supported Versions File {0} is empty".format(self.supported_versions_file))
            BootstrapBase.exit_application(99)

        try:
            value = self.edf_supported_versions = self.k8s_edf_versions[self.channel]
            if type(value) is not list or (type(value) is list and not len(value)):
                Log.error("'{0}' channel has no supported versions. Refer to edf_gke_versions_example.yaml "
                          "file under bootstrap/src/mapr/clouds/google/".format(self.channel))
                BootstrapBase.exit_application(104)
        except KeyError:
            Log.error("channel '{0}' is not listed in file".format(self.channel))
            BootstrapBase.exit_application(107)

    def get_name(self):
        return GoogleCloud.NAME

    def is_enabled(self):
        return self.enabled

    def is_available(self):
        if not self.enabled:
            return False

        if self.available is None:
            Log.info("Checking Google cloud availability. One moment...", True)
            results, status = OSCommand.run2(["command -v gcloud", "gcloud compute instances list"])
            self.available = True if status == 0 else False

            if not self.available:
                Log.warning("Google Cloud SDK not found or not configured correctly. Quit bootstrapper, install and "
                            "configure Google Cloud SDK and restart bootstrapper. See: https://cloud.google.com/sdk/. "
                            "More information on the error in the bootstrapper log here: " + Log.get_log_filename())
                Log.warning(results)
            else:
                result, status = self.invoke_gcloud("version")
                Log.info("gcloud SDK information; Status: {0}, Version: {1}".format(status, result))

        return self.available

    def setup_cloud_usage(self):
        usage = self.prompts.prompt_choices("Choose Kubernetes cluster usage type", GoogleUsages.get_usage_names(),
                                            default=GoogleUsages.USAGE_COMPUTE_NAME, key_name="CLOUD_USAGE")
        self._usage = GoogleUsages(usage)

    def build_cloud(self):
        self.zone = self._usage.get("Zone")
        self.image_type = self._usage.get("ImageType")
        self.disk_type_on_node = self._usage.get("DiskTypeOnNode")
        self.block_disk_size = self._usage.get("BlockDiskSize")
        self.os_disk_size = self._usage.get("OSDiskSize")
        self.k8s_version = self._usage.get("K8SVersion")
        self.k8s_alpha_version = self._usage.get("K8SAlphaVersion")
        self.nodes = self._usage.get("Nodes")
        self.disks = self._usage.get("Disks")
        self.instance_type = self._usage.get("InstanceType")

        self.cluster_name = self.prompts.prompt("Enter cluster name", self.cluster_name, key_name="GKE_CLUSTER_NAME")
        self.nodes = self.prompts.prompt_integer("Enter number of nodes", self.nodes, 1, key_name="GKE_NODE_COUNT")
        self.disks = self.prompts.prompt_integer(
            "Enter number of raw SSD disks for MapR FS. Each disk will be a fixed {0}GB".format(self.block_disk_size),
            self.disks, 1, key_name="GKE_NUM_DISKS")
        self.instance_type = self.prompts.prompt("GCE compute instance type?", self.instance_type,
                                                 key_name="GKE_INSTANCE_TYPE")
        self.zone = self.prompts.prompt("GCE Zone to deploy into?", self.zone, key_name="GKE_ZONE")
        if self.alpha:
            self.k8s_version = self.prompts.prompt("Kubernetes version?", self.k8s_alpha_version,
                                                   key_name="GKE_K8S_VERSION")
        else:
            self.gke_channel_support = self.prompts.prompt_boolean("Do you want to enable GKE Channel support",
                                                                   True, key_name="GKE_CHANNEL_SUPPORT")

            if not self.gke_channel_support:
                self.k8s_version = self.prompts.prompt("Kubernetes version?", self.k8s_version,
                                                       key_name="GKE_K8S_VERSION")
            else:
                self.channel = self.prompts.prompt_choices("Choose GKE release Channel",
                                                           GoogleCloud.GKE_RELEASE_CHANNELS,
                                                           default=GoogleCloud.GKE_RELEASE_CHANNELS[1],
                                                           key_name="GKE_RELEASE_CHANNEL")
                Log.info("Release channel chosen '{0}'".format(self.channel))
                self.validate_versions_file()
                supported_versions = self.get_supported_versions()
                self.k8s_version = self.prompts.prompt_choices("Choose Kubernetes version", supported_versions,
                                                               default=supported_versions[-1],
                                                               key_name="GKE_K8S_VERSION")
        self.project = self.prompts.prompt("GCE project id?", self.project, key_name="GKE_PROJECT_ID")
        self.user = self.prompts.prompt("GCE user id?", self.user, key_name="GKE_USER")
        # self.image_type = self.prompts.prompt("GKE image type?", self.image_type)
        Log.info("Using GCE compute image type: {0}".format(self.image_type), True)
        if self.alpha:
            Log.info("Using alpha Kubernetes version", True)
        else:
            Log.info("Using non-alpha Kubernetes version", True)

        if not self.prompts.prompt_boolean("Ready to create Google GKE cluster. Do you want to continue?", True,
                                           key_name="GKE_CREATE"):
            Log.error("Exiting since user is not ready to continue")
            BootstrapBase.exit_application(100)

        before = time.time()
        self.create_k8s_cluster()
        after = time.time()
        diff = int(after - before)
        Log.info("Cluster creation took {0}m {1}s".format(diff / 60, diff % 60), True)

    def create_k8s_cluster(self):
        Log.info("Creating cluster with {0} nodes of type {1} with {2} local ssd(s) of size {3}GB...".
                 format(self.nodes, self.instance_type, self.disks, self.block_disk_size), True)

        args = "--zone {0} ".format(self.zone)
        if not self.alpha and self.gke_channel_support:
            args += "--release-channel {0} ".format(self.channel)
        args += "--cluster-version {0} ".format(self.k8s_version)
        args += "--machine-type {0} ".format(self.instance_type)
        args += "--image-type {0} ".format(self.image_type)
        args += "--disk-size {0} ".format(self.os_disk_size)
        args += "--disk-type {0} ".format(self.disk_type_on_node)
        args += "--num-nodes {0} ".format(self.nodes)
        args += "--network default "
        args += "--enable-stackdriver-kubernetes "
        args += "--metadata disable-legacy-endpoints=true "
        args += "--no-enable-ip-alias "
        if self.alpha:
            args += "--enable-kubernetes-alpha "
            args += "--no-enable-autorepair "
            args += "--no-enable-autoupgrade "
        elif not self.gke_channel_support:
            args += "--no-enable-autoupgrade "
        args += "--subnetwork default "
        args += "--scopes https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append "
        self.invoke_cluster(args)

        Log.info("Node log follows after cluster creation. One moment...", True)
        cmd = "container clusters get-credentials {0} --zone {1} --project {2}".format(self.cluster_name, self.zone,
                                                                                       self.project)
        result, status = self.invoke_gcloud(cmd)
        Log.info(result, True)

        # TODO Got to be a better way to get this filtered list
        result, status = OSCommand.run2("kubectl get nodes | grep Ready | cut -d' ' -f1")
        if status != 0:
            Log.error("Could not get list of nodes: {0}: {1}".format(status, result))
            BootstrapBase.exit_application(101)

        nodes = result.split("\n")
        if len(nodes[-1]) == 0:
            nodes = nodes[:-1]

        Log.info("After cluster creation, {0} node(s) were found".format(len(nodes)), True)
        all_threads = list()
        for node in nodes:
            t = Thread(target=self.create_disks_and_attach, args=(node,), name=node)
            all_threads.append(t)
            t.start()
            time.sleep(0.05)

        for thread in all_threads:
            thread.join(timeout=10 * 60)
            if thread.is_alive():
                Log.error("Thread for node {0} did not complete in the supplied time limit".format(thread.name))

    def create_disks_and_attach(self, node):
        # Create a disk list
        disk_list = ""
        for i in range(0, self.disks):
            disk_list += "{0}-disk-{1} ".format(node, i)

        Log.info("Creating and attaching disk(s) for node {0}. One moment...".format(node), True)

        result, status = self.invoke_gcloud(
            "compute disks create --size {0}GB --type pd-ssd --project {1} --zone {2} {3}".format(self.block_disk_size,
                                                                                                  self.project,
                                                                                                  self.zone, disk_list))
        Log.info("Created {0} disk(s) for node {1}".format(self.disks, node))
        Log.debug(result)

        for i in range(0, self.disks):
            disk_name = "{0}-disk-{1} ".format(node, i)
            result, status = self.invoke_gcloud(
                "compute instances attach-disk {0} --disk {1} --project {2} --zone {3}".format(node, disk_name,
                                                                                               self.project, self.zone))
            Log.info("Added disk {0} to node {1}".format(disk_name, node))
            Log.debug(result)

            result, status = self.invoke_gcloud(
                "compute instances set-disk-auto-delete {0} --disk {1} --project {2} --zone {3}".format(node, disk_name,
                                                                                                        self.project,
                                                                                                        self.zone))
            Log.info("Set set-disk-auto-delete on disk {0}".format(disk_name))
            Log.debug(result)

        Log.info("Created and attached disk(s) for node {0}".format(node), True)

    def configure_cloud(self):
        cmd = GoogleCloud.CMD_ROLE_BINDING.format(self.user)
        Log.info("Now we will configure RBAC for your kubernetes env...", True)
        Log.info("Binding cluster-admin role to GCE user: {0}...".format(self.user), True)
        response, status = OSCommand.run2(cmd)
        if status != 0:
            Log.error("Could not bind cluster-admin role: {0}:{1}", status, response)
        Log.info("Configured GKE permissions", True)

    def get_supported_versions(self):
        cmd = 'container get-server-config --zone={0} --flatten="channels" --filter="channels.channel={1}" ' \
              ' --format="yaml(channels.channel,channels.validVersions)"'.format(self.zone, self.channel)
        response, status = self.invoke_gcloud(cmd)
        if status != 0:
            Log.error("Could not fetch supported k8s versions from google cloud: {0}:{1}", status, response)
            BootstrapBase.exit_application(102)
        gke_supported_versions = []
        response = response.split("\n")
        Log.info("GKE version support response {0}".format(response))
        for version in response:
            version_match = re.search("(\d+.\d+.\d+).*", version)
            #       version_match = re.search("\d+.\d+", version)
            if version_match is None:
                continue
            gke_supported_versions.append(version_match.group(0))
        if self.edf_supported_versions is None:
            Log.error("No versions listed for channel {0} in file".format(self.channel))
            BootstrapBase.exit_application(103)
        common_versions = []
        for version in self.edf_supported_versions:
            for gke_version in gke_supported_versions:
                if version in gke_version:
                    common_versions.append(gke_version)
        Log.info("EDF support versions for channel '{0}' is {1}. GKE support versions is {2}".format(self.channel,
                                                                                                     self.edf_supported_versions,
                                                                                                     gke_supported_versions))
        if len(common_versions):
            Log.info("Common supported versions {0}".format(common_versions))
            common_versions.sort(key=LooseVersion)
            return common_versions
        else:
            Log.error("No common versions found between edf and gke supported versions for chosen channel '{0}'. \n"
                      "Consider adding support for a new version of K8s that GKE supports.".format(self.channel))
            BootstrapBase.exit_application(104)

    def invoke_cluster(self, args):
        cmd = "container --project {0} clusters create {1} {2}".format(self.project, self.cluster_name, args)
        Log.info("kubernetes version = {0}".format(self.k8s_version), True)
        Log.info("Creating GKE environment via the following command: gcloud {0}".format(cmd), True)
        Log.info("Create log follows...")
        result, status = self.invoke_gcloud(cmd)
        Log.info(result, True)

    @staticmethod
    def invoke_gcloud(cmd):
        response, status = OSCommand.run2("gcloud {0}".format(cmd))
        if status != 0:
            Log.error("Could not create GKE Cluster: {0}: {1}".format(status, response))
            print("")
            Log.error(
                "The most common cause for failure is not having the latest gcloud SDK. The gcloud SDK must be 276.0.0 or greater.")
            BootstrapBase.exit_application(106)
        return response, status
