import os
import base64

from common.const import Constants
from common.yamlize import Yamlize
from common.mapr_logger.log import Log
from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class LDAP(OperationsBase):
    def __init__(self, prompts):
        super(LDAP, self).__init__()
        self.prompts = prompts
        self.use_sssd = "true"
        self.username = Constants.USERNAME
        self.password = Constants.PASSWORD
        self.groupname = Constants.GROUPNAME
        self.userid = Constants.USERID
        self.groupid = Constants.GROUPID
        self.admin_username = Constants.ADMIN_USERNAME
        self.admin_groupname = Constants.ADMIN_GROUPNAME
        self.admin_userid = Constants.ADMIN_USERID
        self.admin_groupid = Constants.ADMIN_GROUPID
        self.admin_password = Constants.ADMIN_PASS
        self.mysql_user = Constants.MYSQL_USER
        self.mysql_pass = Constants.MYSQL_PASS
        self.ldapadmin_user = Constants.LDAPADMIN_USER
        self.ldapadmin_pass = Constants.LDAPADMIN_PASS
        self.ldapbind_user = Constants.LDAPBIND_USER
        self.ldapbind_pass = Constants.LDAPBIND_PASS
        self.auth_type = Constants.AUTH_TYPES.EXAMPLE_LDAP
        self.ldap_dir = os.path.abspath(os.path.join(self.prereq_dir, "ldap"))
        if not os.path.exists(self.ldap_dir):
            raise NotFoundException(self.ldap_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.ldap_dir, "ldap-namespace.yaml")
        ldap_namespace_yaml_file = YamlFile("ldap-namespace", "Example LDAP Namespace", file_name, "ldap_namespace_component")
        self.yamls.append(ldap_namespace_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-imagepullsecret.yaml")
        ldap_imagepullsecret_yaml_file = YamlFile("ldap-imagepullsecret", "secret to pull images for Example LDAP Namespace", file_name, "ldap_imagepullsecret_component")
        self.yamls.append(ldap_imagepullsecret_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-seed-secret.yaml")
        ldap_seed_secret_yaml_file = YamlFile("ldap-seed-secret", "ldif secret for Example LDAP, file_name", file_name, "ldap_components")
        self.yamls.append(ldap_seed_secret_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-config-cm.yaml")
        ldap_config_cm_yaml_file = YamlFile("ldap-config-cm", "Example LDAP Configuration ConfigMap", file_name, "ldap_components")
        self.yamls.append(ldap_config_cm_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-sa.yaml")
        ldap_sa_yaml_file = YamlFile("ldap-sa", "Example LDAP Service Account", file_name, "ldap_components")
        self.yamls.append(ldap_sa_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-svc.yaml")
        ldap_svc_yaml_file = YamlFile("ldap-svc", "Example LDAP Service", file_name, "ldap_components")
        self.yamls.append(ldap_svc_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldap-ss.yaml")
        ldap_ss_yaml_file = YamlFile("ldap-ss", "Example LDAP StatefulSet", file_name, "ldap_components")
        self.yamls.append(ldap_ss_yaml_file)

        file_name = self.check_exists(self.ldap_dir, "ldapcert-secret.yaml")
        ldapcert_secret_yaml_file = YamlFile("ldapcert-secret", "Secure LDAP Certs Secret", file_name, "ldap_secret_component")
        self.yamls.append(ldapcert_secret_yaml_file)
        return True

    def install_exampleldap(self, upgrade_mode=False):
        installable_yaml_types = ["ldap_namespace_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

        installable_yaml_types = ["ldap_imagepullsecret_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

        self._run("kubectl delete secret system-user-secrets -n {0} --ignore-not-found".
                  format(Constants.EXAMPLE_LDAP_NAMESPACE))
        Log.info(os.linesep + "Creating user secrets for Example LDAP...", True)

        if self.create_sys_user_secret(Constants.EXAMPLE_LDAP_NAMESPACE):
            Log.info("Created user secrets for Example LDAP.")

        installable_yaml_types = ["ldap_components"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_exampleldap(self):

        uninstallable_yaml_types = ["ldap_components", "ldap_imagepullsecret_component", "ldap_namespace_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        Log.info(os.linesep + "Deleting user secrets for Example LDAP...", True)
        if self.delete_sys_user_secret(Constants.EXAMPLE_LDAP_NAMESPACE):
            Log.info("Deleted user secrets for Example LDAP.")

    def check_auth_type(self):
        print(os.linesep)
        Log.info("Please choose a user authentication configuration option from the three listed:",  True)
        Log.info("EXAMPLE ) Use an example OpenLDAP container (not for production use)", True)
        Log.info("EXISTING) Use an an existing LDAP server in your environment",  True)
        Log.info("NONE    ) Use raw Linux users in each container (for debugging purposes only)", True)
        options = ['EXAMPLE', 'EXISTING', 'NONE']
        choice = self.prompts.prompt_choices("Choose an option", options, 'EXAMPLE', key_name="LDAP_OPTION")

        sel_dict = {
            'EXISTING': self.external_ldap,
            'NONE': self.raw_linux_users,
            'EXAMPLE': self.example_ldap
        }

        callable_fn = sel_dict.get(choice)
        result = callable_fn()
        return result

    def external_ldap(self):
        print("")
        Log.info("Please answer the following questions:", True)
        # self.adminuid = self.prompts.prompt("What user uid in your LDAP would you like to grant administrative rights?",
        #                                     getpass.getuser(), False, key_name="ADMIN_USER")
        self.auth_type = Constants.AUTH_TYPES.CUSTOM_LDAP
        print("")
        self.admin_username = self.prompts.prompt("What admin user account from your authentication provider would like us to create and register as data admin during pod"
                                            "initialization?", self.admin_username, False, key_name="ADMIN_USER")
        self.admin_userid = self.prompts.prompt("What is admin user's uid?", self.admin_userid, False, key_name="ADMIN_UID")
        Log.info("The data fabric uses common ldap.conf, sssd.conf, and any provided certs when bringing up pods"
                 ".", True)
        OperationsBase.replace_dict["{ldap-file}"] = \
            self.prompts.prompt_file("Please provide an ldap.conf file to import", "ldap.conf", False,
                                     key_name="LDAP_CONF")
        with open(OperationsBase.replace_dict["{ldap-file}"]) as readfile:
            file_contents = readfile.read()
        OperationsBase.replace_dict["{ldap-file-contents}"] = Yamlize.genConfigMapValue(file_contents)

        OperationsBase.replace_dict["{sssd-file}"] =\
            self.prompts.prompt_file("Please provide an sssd.conf file to import", "sssd.conf",
                                     False, key_name="SSSD_CONF")
        with open(OperationsBase.replace_dict["{sssd-file}"]) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{sssd-file-encoded}"] = base64.b64encode(data_bytes)
        self.use_sssd = "true"
        Log.info("Optionally, if your LDAP/SSSD setup is configured to verify TLS certs, enter an individual or "
        "bundle CA certificate file to include.  Hit Enter (blank file name) to skip.", True)
        new_line = ""
        OperationsBase.replace_dict["{ldapcert-file-encoded}"] = ""
        file_name = self.prompts.prompt_file(" File to import", newline=False,
                                            key_name="SERVER_CERT", allow_blank=True)
        if not (file_name is None or file_name == "None"):
            with open(file_name) as readfile:
                file_contents = readfile.read()
            data_bytes = file_contents.encode("utf-8")
            data_string = base64.b64encode(data_bytes).decode('utf-8')
            file_only = os.path.basename(file_name)
            data_string = file_only + ": " + data_string + new_line
            OperationsBase.replace_dict["{ldapcert-file-encoded}"] =\
                OperationsBase.replace_dict["{ldapcert-file-encoded}"] + data_string
        self.admin_groupname = ""
        self.admin_groupid = 0
        self.admin_password = ""
        return True

    def raw_linux_users(self):
        print("")
        Log.info("Please answer the following questions:", True)
        self.admin_username = self.prompts.prompt("What admin user account would you would like us to create and register during pod"
                                            "initialization?", self.admin_username, False, key_name="ADMIN_USER")
        self.admin_userid = self.prompts.prompt("What is admin user's uid?", self.admin_userid, False, key_name="ADMIN_UID")
        self.admin_groupname = self.prompts.prompt("A new group will be created, what name would you like?", self.admin_groupname,
                                             False, key_name="ADMIN_GROUP")
        self.admin_groupid = self.prompts.prompt("What is admin user's group account gid?", self.admin_groupid, False, key_name="ADMIN_GID")

        self.admin_password = self.prompts.prompt("Admin user account password", self.password, True, key_name="ADMIN_PASSWORD")
        self.auth_type = Constants.AUTH_TYPES.RAW_LINUX_USERS
        # data_string = "#empty - MapR using raw linux users"
        # data_bytes = data_string.encode("utf-8")
        raw_linux_str_as_bytes = str.encode("#empty - MapR using raw linux users")
        OperationsBase.replace_dict["{sssd-file-encoded}"] = base64.b64encode(raw_linux_str_as_bytes)
        OperationsBase.replace_dict["{ldap-file-contents}"] =\
            Yamlize.genConfigMapValue("#empty - MapR using rawlinux users")
        self.use_sssd = "false"
        return True

    def example_ldap(self):
        print("")
        Log.info(os.linesep + "An example LDAP service will be created in the hpe-ldap namespace.  The user account "
                 "the MapR cluster will use will have the username/password \'mapr/mapr\'.  The group will be \'mapr\'."
                 " The admin account that will be created will be \'admin/mapr\'.  Lastly, a readonly user account will"
                 " be created as 'readonly/mapr'.", True)

        # Place the correct values into the replace dictionary so that yaml generation will do substitutions
        self.auth_type = Constants.AUTH_TYPES.EXAMPLE_LDAP
        self.use_sssd = "true"
        self.admin_username = ""
        self.admin_groupname = ""
        self.admin_userid = 0
        self.admin_groupid = 0
        self.admin_password = ""
        return True

    def install_secure_components(self, upgrade_mode=False):
        Log.info(os.linesep + "Creating Secure System User Secret...", True)
        self.delete_sys_user_secret('hpe-secure')
        if self.create_sys_user_secret('hpe-secure'):
            Log.info("Created secure system user secret.")
        if "{ldapcert-file-encoded}" in OperationsBase.replace_dict:
            installable_yaml_types = ["ldap_secret_component"]
            self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_secure_components(self):
        Log.info(os.linesep + "Deleting Secure System User Secret...", True)
        if self.delete_sys_user_secret('hpe-secure'):
            Log.info("Deleted secure system user secret.")
            uninstallable_yaml_types = ["ldap_secret_component"]
            self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

    def create_sys_user_secret(self, namespace):
        cmd = 'kubectl create secret generic system-user-secrets -n ' + namespace + ' ' \
              '--from-literal="USE_SSSD=' + self.use_sssd + '" ' \
              '--from-literal="MAPR_USER=' + self.username + '" ' \
              '--from-literal="MAPR_PASSWORD=' + self.password + '" ' \
              '--from-literal="MAPR_CLUSTER_USER=' + self.username + '" ' \
              '--from-literal="MAPR_CLUSTER_PASSWORD=' + self.password + '" ' \
              '--from-literal="MAPR_GROUP=' + self.groupname + '" ' \
              '--from-literal="MAPR_UID=' + str(self.userid) + '" ' \
              '--from-literal="MAPR_GID=' + str(self.groupid) + '" ' \
              '--from-literal="MYSQL_USER=' + self.mysql_user + '" ' \
              '--from-literal="MYSQL_PASSWORD=' + self.mysql_pass + '" ' \
              '--from-literal="LDAPADMIN_USER=' + self.ldapadmin_user + '" ' \
              '--from-literal="LDAPADMIN_PASSWORD=' + self.ldapadmin_pass + '" ' \
              '--from-literal="LDAPBIND_USER=' + self.ldapbind_user + '" ' \
              '--from-literal="LDAPBIND_PASSWORD=' + self.ldapbind_pass + '" ' \
              '--from-literal="CUSTOMER_GID=' + str(self.admin_groupid) + '" ' \
              '--from-literal="CUSTOMER_UID=' + str(self.admin_userid) + '" ' \
              '--from-literal="CUSTOMER_USER=' + self.admin_username + '" ' \
              '--from-literal="CUSTOMER_GROUP=' + self.admin_groupname + '" ' \
              '--from-literal="CUSTOMER_PASSWORD=' + self.admin_password + '" '
        return self._run(cmd)

    def delete_sys_user_secret(self, namespace):
        cmd = 'kubectl delete secret system-user-secrets -n ' + namespace + ' --ignore-not-found'
        return self._run(cmd)
