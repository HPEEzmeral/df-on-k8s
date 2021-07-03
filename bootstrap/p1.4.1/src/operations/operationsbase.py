import os
import base64
import tempfile
import time

from common.const import Constants
from common.file_utils import FileUtils
from common.yamlize import Yamlize
from common.mapr_logger.log import Log
from common.os_command import OSCommand
from common.mapr_exceptions.ex import NotFoundException
from shutil import copy2

from operations.upgrade_strategy import Apply


class OperationsBase(object):
    KUBECTL_APPLY = "kubectl apply -f"
    KUBECTL_DELETE = "kubectl delete -f"
    KUBECTL_GET = "kubectl get"
    KUBECTL_CERT = "kubectl certificate"
    KUBECTL_RESTART_DEPLOYMENT = "kubectl rollout restart deployment"
    KUBECTL_WAIT_DEPLOYMENT = "kubectl wait --for=condition=available deployment/{0} -n {1} --timeout={2}s"
    KUBECTL_CHECK_IF_NAMESPACE_EXISTS = "kubectl get namespaces | grep {0} | wc -l"
    OC_APPLY = "oc apply -f"
    OC_DELETE = "oc delete -f"
    KUBECTL_LABEL_NODE = "kubectl label node --overwrite {0} \"{1}={2}\""
    GIT_FETCH_SUBMODULE = "git submodule update --init --remote -- "
    csi_repo = Constants.CSI_REPO
    kdf_rep = Constants.KDF_REPO
    kubeflow_repo = Constants.KUBEFLOW_REPO
    operator_repo = Constants.OPERATOR_REPO
    local_path_provisioner_repo = Constants.LOCAL_PATH_PROVISIONER_REPO
    kfctl_hcp_istio_repo = Constants.KFCTL_HSP_ISTIO_REPO
    busybox_repo = Constants.BUSYBOX_REPO
    kubelet_directory = Constants.KUBELET_DIR
    fake_labels = "true"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prereq_dir = os.path.abspath(os.path.join(base_dir, "../../prereqs"))
    if not os.path.exists(prereq_dir):
        raise NotFoundException(prereq_dir)
    customize_dir = os.path.abspath(os.path.join(base_dir, "../../customize"))
    if not os.path.exists(customize_dir):
        raise NotFoundException(customize_dir)
    auth_dir = os.path.abspath(os.path.join(customize_dir, "auth"))
    if not os.path.exists(auth_dir):
        raise NotFoundException(auth_dir)
    replace_dict = dict()

    def __init__(self):
        self.is_openshift = False
        self.log_config_file = os.path.join(OperationsBase.base_dir, Constants.LOGGER_CONF)
        self.yamls = list()
        self.custom_upgrade_strategies = dict()

    @staticmethod
    def _run(cmd):
        response, status = OSCommand.run2(cmd)
        if status != 0:
            Log.error("Could not run {0}: {1}:{2}".format(cmd, str(status), response))
            return False
        return True

    @staticmethod
    def _run_and_return_response(cmd, print_error=True):
        response, status = OSCommand.run2(cmd)
        if status != 0:
            if print_error:
                Log.error("Could not run {0}: {1}:{2}".format(cmd, str(status), response))
            return None
        return response

    @staticmethod
    def run_get(cmd, print_error=True):
        cmd = "{0} {1}".format(OperationsBase.KUBECTL_GET, cmd)
        response, status = OSCommand.run2(cmd)
        if status != 0:
            if print_error:
                Log.error("Could not run {0}: {1}:{2}".format(cmd, str(status), response))
        return response, status

    @staticmethod
    def check_exists(adir, ayaml, suppressexception=False):
        abs_file = os.path.join(adir, ayaml)
        if not os.path.exists(abs_file) or not os.path.isfile(abs_file):
            if not suppressexception:
                raise NotFoundException("{0} must exist and must be a file".format(abs_file))
        return abs_file

    @staticmethod
    def delete_temp_yaml(yaml_file):
        os.remove(yaml_file)

    @staticmethod
    def run_label_mapr_node(node_name, label, is_mapr_node, print_error=True):
        cmd = OperationsBase.KUBECTL_LABEL_NODE.format(node_name, label, str(is_mapr_node).lower())
        response, status = OSCommand.run2(cmd)
        if status != 0:
            if print_error:
                Log.error("Could not run {0}: {1}:{2}".format(cmd, str(status), response))
        return response, status

    @staticmethod
    def load_replace_dict():
        OperationsBase.replace_dict["{ldap-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ldap.conf")
        OperationsBase.replace_dict["{sssd-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-sssd.conf")
        OperationsBase.replace_dict["{ldap-seed-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ldap-seed.ldif")
        OperationsBase.replace_dict["{image-pull-secret-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-imagepullsecret")
        OperationsBase.replace_dict["{ssh-auth-keys-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ssh-authorizedkeys")
        OperationsBase.replace_dict["{ssh-priv-keyring-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ssh-private-keyring")
        OperationsBase.replace_dict["{ssh-pub-keyring-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ssh-public-keyring")
        OperationsBase.replace_dict["{ssl-keystore-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ssl-keystore")
        OperationsBase.replace_dict["{ssl-truststore-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-ssl-truststore")
        OperationsBase.replace_dict["{csi-ticket-file}"] =\
            OperationsBase.check_exists(OperationsBase.auth_dir, "example-csi-ticket")

        with open(OperationsBase.replace_dict["{sssd-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{sssd-file-encoded}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{ldap-file}"]) as readfile:
            file_contents = readfile.read()
        OperationsBase.replace_dict["{ldap-file-contents}"] = Yamlize.genConfigMapValue(file_contents)

        with open(OperationsBase.replace_dict["{ldap-seed-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ldap-seed-file-encoded}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{image-pull-secret-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{image-pull-secret}"] = base64.b64encode(data_bytes)
        with open(OperationsBase.replace_dict["{ssh-auth-keys-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ssh-auth-keys}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{ssh-priv-keyring-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ssh-priv-keyring}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{ssh-pub-keyring-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ssh-pub-keyring}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{ssl-keystore-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ssl-keystore}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{ssl-truststore-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{ssl-truststore}"] = base64.b64encode(data_bytes)

        with open(OperationsBase.replace_dict["{csi-ticket-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{csi-ticket}"] = base64.b64encode(data_bytes)

    def run_kubectl_get(self, get_str):
        cmd = "{0} {1}".format(OperationsBase.KUBECTL_GET, get_str)
        result = self._run_and_return_response(cmd)
        return result

    def get_yaml(self, yaml_file_path):
        if yaml_file_path is None:
            raise NotFoundException(
                "The key '{0}' does not have an entry in the yamls dictionary".format(yaml_file_path))
        yaml_file, changed = FileUtils.replace_yaml_value(yaml_file_path, OperationsBase.replace_dict)
        return yaml_file, changed

    def run_kubectl_apply(self, yaml_obj):
        yaml_file, changed = self.get_yaml(yaml_obj.file_path)
        if self.is_openshift:
            applyop = OperationsBase.OC_APPLY
        else:
            applyop = OperationsBase.KUBECTL_APPLY
        cmd = "{0} {1}".format(applyop, yaml_file)
        result = self._run(cmd)

        if changed:
            if not result:
                self.save_temp_yaml(yaml_file)
            self.delete_temp_yaml(yaml_file)
        return result

    def run_kubectl_delete(self, yaml_obj, ignore_not_found=False):
        yaml_file, changed = self.get_yaml(yaml_obj.file_path)
        if yaml_file is None:
            raise NotFoundException(
                "The key '{0}' does not have an entry in the yamls dictionary".format(yaml_obj.file_path))
        if self.is_openshift:
            deleteop = OperationsBase.OC_DELETE
        else:
            deleteop = OperationsBase.KUBECTL_DELETE
        if ignore_not_found:
            ignore_not_found_option = "--ignore-not-found"
            cmd = "{0} {1} {2}".format(deleteop, yaml_file, ignore_not_found_option)
        else:
            cmd = "{0} {1}".format(deleteop, yaml_file)
        result = self._run(cmd)
        if changed:
            if not result:
                self.save_temp_yaml(yaml_file)
            self.delete_temp_yaml(yaml_file)
        return result

    def save_temp_yaml(self, yaml_file):
        basename = os.path.basename(Log.get_log_filename())
        log_split = basename.split('.')
        log_base = os.path.dirname(Log.get_log_filename())
        log_dir = log_split[len(log_split) - 2]
        full_log_dir = os.path.join(log_base, log_dir)
        if not os.path.exists(full_log_dir):
            os.mkdir(full_log_dir)
        copy2(yaml_file, full_log_dir)
        Log.info("Preserving " + yaml_file + " in case needed for debugging")

    def run_kubectl_certificate(self, cert_str):
        cmd = "{0} {1}".format(OperationsBase.KUBECTL_CERT, cert_str)
        result = self._run(cmd)
        return result

    def run_kubectl_restart(self, deployment, namespace):
        cmd = "{0} {1} -n {2}".format(OperationsBase.KUBECTL_RESTART_DEPLOYMENT, deployment, namespace)
        result = self._run(cmd)
        return result

    def run_kubectl_wait_deployment(self, deployment, namespace, timeout):
        cmd = OperationsBase.KUBECTL_WAIT_DEPLOYMENT.format(deployment, namespace, timeout)
        result = self._run(cmd)
        return result

    def run_kubectl_check_if_namespace_exists(self, namespace):
        cmd = OperationsBase.KUBECTL_CHECK_IF_NAMESPACE_EXISTS.format(namespace)
        result = self._run_and_return_response(cmd)
        return int(result) == 1

    def run_git_fetch_submodule(self, submodule):
        cmd = OperationsBase.GIT_FETCH_SUBMODULE + submodule
        result = self._run(cmd)
        return result

    def install_components(self, installable_yaml_types=None, upgrade_mode=False):
        if installable_yaml_types is None:
            installable_yaml_types = []
        log_prefix_str = "Creating "
        success_log_prefix_str = "Created "
        if upgrade_mode:
            log_prefix_str = "Updating "
            success_log_prefix_str = "Updated "

        for yaml_file_obj in self.yamls:
            if yaml_file_obj.type in installable_yaml_types:
                if not upgrade_mode:  # installing component
                    Log.info(os.linesep + log_prefix_str + yaml_file_obj.file_name + " ...", True)
                    if self.run_kubectl_apply(yaml_file_obj):
                        Log.info(success_log_prefix_str + yaml_file_obj.file_name + ".")
                elif upgrade_mode and yaml_file_obj.is_upgradable:  # upgrading component
                    Log.info(os.linesep + log_prefix_str + yaml_file_obj.file_name + " ...", True)
                    strategy = self._get_upgrade_strategy(yaml_file_obj)
                    if strategy.upgrade(yaml_file_obj):
                        Log.info(success_log_prefix_str + yaml_file_obj.file_name + ".")

    def uninstall_components(self, uninstallable_yaml_types=None):
        if uninstallable_yaml_types is None:
            uninstallable_yaml_types = []
        log_prefix_str = "Deleting "
        success_log_prefix_str = "Deleted "
        for yaml_file_obj in reversed(self.yamls):
            if yaml_file_obj.type in uninstallable_yaml_types:
                Log.info(os.linesep + log_prefix_str + yaml_file_obj.file_name+" ...", True)
                if self.run_kubectl_delete(yaml_file_obj, yaml_file_obj.ignore_not_found):
                    Log.info(success_log_prefix_str + yaml_file_obj.file_name+".")

    def restart_deployment(self, deployment, namespace):
        log_postfix_str = "deployment {0} in namespace {1}".format(deployment, namespace)
        Log.info("Restarting " + log_postfix_str)
        if self.run_kubectl_restart(deployment, namespace):
            Log.info("Restarted " + log_postfix_str)
        else:
            Log.error("Could not restart " + log_postfix_str)

    def wait_deployment_available(self, deployment, namespace, timeout, interval=10):
        log_postfix_str = "deployment {0} in namespace {1}".format(deployment, namespace)
        Log.info("Waiting " + log_postfix_str + " to become ready")
        start = time.time()
        while time.time() - start < timeout:
            if self.run_kubectl_check_if_namespace_exists(namespace):
                if self.run_kubectl_wait_deployment(deployment, namespace,
                                                    timeout - (time.time() - start)):
                    Log.info("Started " + log_postfix_str)
                    return True
            else:
                time.sleep(interval)
        Log.error("Timeout waiting " + log_postfix_str + " to become ready")
        return False

    def copy_hpe_pull_secrets_to_ns(self, namespace):
        response, status = OSCommand.run2('kubectl get secret hpe-imagepull-secrets -n hpe-system -o yaml')
        if status != 0:
            Log.error("Could not get pull secret: {0}".format(response))
            return False
        pull_secret = response.replace("namespace: hpe-system", "namespace: {0}".format(namespace))

        response, status = OSCommand.run2('kubectl create ns {0}'.format(namespace))
        if status != 0:
            Log.error("Could not create namespace {0}: {1}".format(namespace, response))
            return False

        with tempfile.NamedTemporaryFile(mode="wt", suffix=".yaml") as fp:
            fp.write(pull_secret)
            fp.flush()
            if not self._run("kubectl apply -f {0}".format(fp.name)):
                Log.error("Could not add HPE pull secrets to {0} namespace".format(namespace))
                return False

        Log.info("Added HPE pull secrets to {0} namespace".format(namespace))
        return True

    def git_fetch_submodule(self, submodule):
        log_postfix_str = "git submodule " + submodule
        Log.info("Fetching " + log_postfix_str)
        if self.run_git_fetch_submodule(submodule):
            Log.info("Fetched " + log_postfix_str)
            return True
        else:
            Log.error("Could not fetch " + log_postfix_str)
            return False

    def setup_dex_for_ldap_auth(self):
        path_for_script = os.path.join(self.prereq_dir, "kubeflow/dex-cm-ldap.sh")
        result = self._run(path_for_script)
        return result

    def _get_upgrade_strategy(self, yaml_file):
        if yaml_file in self.custom_upgrade_strategies.keys():
            return self.custom_upgrade_strategies[yaml_file]
        return Apply(self)
