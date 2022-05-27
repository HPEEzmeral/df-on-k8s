import os
import json
import yaml
import subprocess
import tempfile
import time

from common.mapr_logger.log import Log
from operations.operationsbase import OperationsBase
from common.mapr_exceptions.ex import NotFoundException
from operations.yamlfile import YamlFile
from common.file_utils import FileUtils

# Purpose:
#  if there is a detected existing Data Fabric this class contains the logic necessary to perform the steps
#  that we document the user do, programmatically.  These are:
#  1. detect the Data Fabric
#  2. run the scripts to bring it offline
#  3. grab a copy of the Data Fabric CR
#  4. modify the copy so that the image tag used is the base tag related to the release the bootstrap is for.
#  5. apply the CR again
#  6. if restart is requested, run the restart process.

class ExistingDfUpdater(OperationsBase):
    MYDIR = os.path.abspath(os.path.dirname(__file__))
    existing_df_name = None
    existing_df_baseimagetag = None
    existing_df_cr_yamlfile = None
    existing_upgrade_supported = False
    new_df_baseimagetag = None

    def __init__(self):
        super(ExistingDfUpdater, self).__init__()

# Private functions
    def __get_new_df_baseimagetag(self):
        # this is hacky but we don't have the baseimagetag defined as a variable in bootstrap
        # we are going to use the tag in the cluster-operator as the Truth of what the current base release tag
        # is for the release this bootstrap is running for.  There is no file or variable that is defined for this
        # at this time, that would be the other option; having tag_updater.py maintain.
        # spec.template.spec.containers.image
        # however we cannot parse this as a yaml file due to the {operator-repo} string that has not substituted into
        # it yet, so we are going to find the line with the prefix pattern in the deploy file:
        image_tag = None
        dataplatform_deploy_file = os.path.abspath(os.path.join(self.prereq_dir, "system-dataplatform",
            "system-deploy-dataplatformoperator.yaml"))
        if not os.path.exists(dataplatform_deploy_file):
            raise NotFoundException(dataplatform_deploy_file)
        #      image: {operator-repo}/clusteroperatorxxxxxxxxx
        with open(dataplatform_deploy_file) as fp:
            for line in fp:
                if "{operator-repo}/clusteroperator" in line:
                    image_split = line.split(':')
                    image_tag = image_split[len(image_split) - 1]
                    image_tag = image_tag.strip()
        Log.info("the new data fabric image tag detected to use as a baseimagetag is " + str(image_tag), False)
        return image_tag

    def __generate_existing_df_cr_yamlfile(self):
        #        with tempfile.NamedTemporaryFile(mode="wt", suffix=".yaml") as fp:
        filename = os.path.join(tempfile.gettempdir(), "existing_datafabric_cr.yaml")
        cmd = "kubectl get dataplatform " + str(self.existing_df_name) + " -o yaml > " + str(filename)
        result, err_code = self._run_and_return_response(cmd, True)
        if not err_code == 0:
            Log.error(os.linesep + "Unable to obtain the existing data fabric cr.  Output was " +
                      str(result), True)
            return None

        # we are going to use this file to potentially make an upgrade.  So we need to delete the metedata/annotations
        # section so that we can just do a bulk string substitution
        with open(filename) as fp:
            try:
                cr_yaml = yaml.load(fp, Loader=yaml.FullLoader)  # Python 3 and newer PyYAML package
            except AttributeError:
                cr_yaml = yaml.load(fp) # Python 2 and older PyYAML package
        del cr_yaml['metadata']['annotations']

        with open(filename, 'w') as file:
            yaml.dump(cr_yaml, file)
        return filename

    def __get_existing_df_baseimagetag(self):
        # spec.baseimagetag
        with open(self.existing_df_cr_yamlfile) as fp:
            try:
                cr_yaml = yaml.load(fp, Loader=yaml.FullLoader)  # Python 3 and newer PyYAML package
            except AttributeError:
                cr_yaml = yaml.load(fp) # Python 2 and older PyYAML package

        image_tag = cr_yaml['spec']['baseimagetag']
        return image_tag

    def __update_existing_df_yaml(self):
        #using the built-in string substitution dict replace function
        #load with any custom string substututions from file, and then also add the tag substitution
        custom_substitutions_file = os.path.abspath(os.path.join(self.base_dir, "../../upgradesubstitutions.json"))
        f = open(custom_substitutions_file)
        data = json.load(f)
        for item in data['substitutions']:
            OperationsBase.replace_dict[item["old"]] = item["new"]
        #now the tag
        OperationsBase.replace_dict[self.existing_df_baseimagetag] = self.new_df_baseimagetag
        #make the substitution
        new_yaml_file, changed = FileUtils.replace_yaml_value(self.existing_df_cr_yamlfile, OperationsBase.replace_dict)
        return new_yaml_file

    def __update_admincli_only(self):
        #patch the CR to upgrade the admincli pod to have access to current upgrade strategy scripts
        Log.info(os.linesep + "Upgrading the Data Fabric admincli pod to obtain the latest upgrade scripts ...",
            True)
        patch ='{"spec": {"core": {"admincli": {"image": "admincli-6.2.0:' + self.new_df_baseimagetag + '"}}}}'
        # patch = "spec:\n  core:\n    admincli:\n      image: admincli-6.2.0:" + self.new_df_baseimagetag
        cmd = "kubectl patch dataplatform " + self.existing_df_name + " --patch '" + patch + "' --type=merge"
        result, err_code = self._run_and_return_response(cmd, True)
        if not err_code == 0:
            Log.error(os.linesep + "Unable to patch the admincli pod image in the existing data fabric cr.  "
                                   "Output was " + str(result), True)
            return False
        return True

    def __wait_for_admincli_ready(self):
        # wait for the admincli pod to become ready to use again for using upgrade scripts
        Log.info(os.linesep + "Waiting up to 30 minutes for the new admincli image to download and pod to become "
                              "ready...", True)
        time.sleep(20)
        cmd = "kubectl wait --for=condition=ready pod/admincli-0 -n " + self.existing_df_name + " --timeout=30m"
        result, err_code = self._run_and_return_response(cmd, True)
        if not err_code == 0:
            Log.error(os.linesep + "The admincli pod did not upgrade in a timely manner.  After resolving "
                                   "the issue causing this, you can run bootstrap upgrade again.", True)
            return False
        return True

    def __is_upgrade_supported(self):
        # TODO - return false if there is a realization that the current bootstrap cannot/should not upgrade
        #        the datafabric due to version issues
        # our image tags start with a timestamp YYYYMMDDhhmm, we can compare that the existing is not in the future
        # the other comparison would be if the existing is too old, but we have none there yet
        #
        return True

# Public functions

    def check(self):
        #get/set the existing df name var
        cmd = 'kubectl get dataplatform -o custom-columns=NAME:.metadata.name | tail -n +2'
        result, err_code = self._run_and_return_response(cmd, False)
        if not result:
            return False
        self.existing_df_name = result.strip()
        #generate existing df yaml and get/set the baseimagetag
        self.existing_df_cr_yamlfile = self.__generate_existing_df_cr_yamlfile()
        if self.existing_df_cr_yamlfile is None:
            return False
        self.existing_df_baseimagetag = self.__get_existing_df_baseimagetag()
        if not self.existing_df_baseimagetag:
            return False
        #run thru a test that we do support offline upgrade from that data fabric release to this one
        self.existing_upgrade_supported = self.__is_upgrade_supported()
        if not self.existing_upgrade_supported:
            return False

        self.new_df_baseimagetag = self.__get_new_df_baseimagetag()
        return True

    def is_existing_df(self):
        if self.existing_df_name:
            return True
        else:
            return False

    def get_existing_upgrade_supported(self):
        return self.existing_upgrade_supported

    def get_existing_df_name(self):
        return self.existing_df_name

    def get_existing_df_baseimagetag(self):
        return self.existing_df_baseimagetag

    def run_update(self, restart_existing_df):
        # sanity check
        if not self.get_existing_upgrade_supported():
            Log.error(os.linesep + "Attempt to upgrade data fabric unsuccessful, it is not upgradable.", True)
        Log.info(os.linesep + "Starting Data Fabric " + self.existing_df_name + " upgrade ...", True)

        if not self.__update_admincli_only():
            return False

        if not self.__wait_for_admincli_ready():
            return False

        Log.info(os.linesep + "Taking the Data Fabric offline gracefully (this can take awhile) ...", True)
        cmd = "kubectl exec -it -n " + self.existing_df_name + " admincli-0 -- /usr/bin/edf shutdown cluster"
        result, err_code = self._run_and_return_response(cmd, False)
        if err_code != 0:
            Log.error(os.linesep + "Unable to shutdown the existing cluster, failed apply the new CR", True)
            return False

        #dbl check the pods are pinned, this is redundant if pins are already there, it is necessary if the pins
        #were never put there to help with keeping pods in place during ECP upgrades, K8 upgrades, etc.
        cmd = "kubectl exec -it -n " + self.existing_df_name + " admincli-0 -- /usr/bin/edf pin-pods"
        result, err_code = self._run_and_return_response(cmd, False)
        if err_code != 0:
            Log.error(os.linesep + "Unable to pin the data fabric pods in place ", True)
            return False

        Log.info(os.linesep + "Upgrading the Data Fabric ...", True)

        #upgrade the objectstore-cm configmap to talk about 2.2.0 in case it
        # 1. exists
        # 2. references 2.0.0 instead
        cmd = "kubectl get configmap objectstore-cm -n " + self.existing_df_name + " -o yaml > /tmp/tmp_objstore_cm.yaml"
        result, err_code = self._run_and_return_response(cmd, False)
        if err_code == 0:
            #there is one
            cmd = "sed -i 's/objectstore-client-2.0.0/objectstore-client-2.2.0/g' /tmp/tmp_objstore_cm.yaml"
            result, err_code = self._run_and_return_response(cmd, False)
            if err_code == 0:
                cmd = "kubectl apply -f /tmp/tmp_objstore_cm.yaml"
                result, err_code = self._run_and_return_response(cmd, False)
                if err_code != 0:
                    Log.error(os.linesep + "Unable to update the objectstore configmap", True)

        #apply new CR
        #we need to get a fresh CR object with the latest modification of admincli updated, change the tags, and apply
        self.existing_df_cr_yamlfile = self.__generate_existing_df_cr_yamlfile()
        if self.existing_df_cr_yamlfile is None:
            return False
        self.existing_df_baseimagetag = self.__get_existing_df_baseimagetag()
        if not self.existing_df_baseimagetag:
            return False
        # modify the existing datafabric CR YAML with the new baseimagetag
        new_yaml_file = self.__update_existing_df_yaml()
        if new_yaml_file is None:
            Log.error(os.linesep + "Unable to continue existing Data Fabric upgrade, unable to generate the new "
                                   "CR", False)
            return False
        cmd = 'kubectl apply -f ' + new_yaml_file
        result, err_code = self._run_and_return_response(cmd, False)
        if err_code != 0:
            Log.error(os.linesep + "Unable to continue existing Data Fabric upgrade, failed apply the new CR", True)
            return False

        #start cluster back up
        if restart_existing_df:
            Log.info(os.linesep + "Bringing the Data Fabric back online...", True)
            cmd = "kubectl exec -it -n " + self.existing_df_name + " admincli-0 -- /usr/bin/edf startup resume"
            result, err_code = self._run_and_return_response(cmd, False)
            if err_code != 0:
                Log.error(os.linesep + "Unable to start back up the existing Data Fabric", False)
                return False
            #we know we need to force bounce ZK and CLDB pods to the latest version because they do not have staefulsets
            #that automatically do that
            cmd = "kubectl delete pods -n " + self.existing_df_name + " -l hpe.com/component=cldb"
            result, err_code = self._run_and_return_response(cmd, False)
            if err_code != 0:
                Log.error(os.linesep + "Unable to restart all the CLDB pods in the existing Data Fabric", True)
            cmd = "kubectl delete pods -n " + self.existing_df_name + " -l hpe.com/component=zk"
            result, err_code = self._run_and_return_response(cmd, False)
            if err_code != 0:
                Log.error(os.linesep + "Unable to restart all the ZK pods in the existing Data Fabric", False)
        return True
