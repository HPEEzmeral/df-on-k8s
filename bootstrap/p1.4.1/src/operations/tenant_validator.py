import os
import subprocess
import base64
import time

from common.mapr_exceptions.ex import NotFoundException
from common.mapr_logger.log import Log
from common.const import Constants
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


# Purpose:
#  functions in this class help stand-up
#  the Tenant  infrastructure
#

class TenantValidator(OperationsBase):
    MYDIR = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):
        super(TenantValidator, self).__init__()
        self.tenant_dir = os.path.abspath(os.path.join(self.prereq_dir, "system-tenant-validator"))
        if not os.path.exists(self.tenant_dir):
            raise NotFoundException(self.tenant_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.tenant_dir, "tenantvalid-csr.yaml")
        tenantvalidator_csr_yaml_file = YamlFile("tenantvalidator-csr", "Tenant Validator Service CSR", file_name,
                                                 "tenantvalidator_csr_component", True, True)
        self.yamls.append(tenantvalidator_csr_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-sa.yaml")
        tenantvalidator_sa_yaml_file = YamlFile("tenantvalidator-sa", "Tenant Validator Service Account", file_name,
                                                "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_sa_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-cr.yaml")
        tenantvalidator_cr_yaml_file = YamlFile("tenantvalidator-cr", "Tenant Validator Cluster Role", file_name,
                                                "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_cr_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-crb.yaml")
        tenantvalidator_crb_yaml_file = YamlFile("tenantvalidator-crb", "Tenant Validator Cluster Role Binding",
                                                 file_name, "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_crb_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-deploy.yaml")
        tenantvalidator_deployment_yaml_file = YamlFile("tenantvalidator-deployment", "Tenant Validator Deployment",
                                                        file_name, "tenantvalidator_deployemt_component", True, True)
        self.yamls.append(tenantvalidator_deployment_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-svc.yaml")
        tenantvalidator_service_yaml_file = YamlFile("tenantvalidator-service", "Tenant Validator Service", file_name,
                                                     "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_service_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-mwhconfig.yaml")
        tenantvalidator_mwc_yaml_file = YamlFile("tenantvalidator-mwc",
                                                 "Tenant Validator Mutating Admission Controller", file_name,
                                                 "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_mwc_yaml_file)

        file_name = self.check_exists(self.tenant_dir, "tenantvalid-vwhconfig.yaml")
        tenantvalidator_vwc_yaml_file = YamlFile("tenantvalidator-vwc",
                                                 "Tenant Validator Validating Admission Controller", file_name,
                                                 "tenantvalidator_components", True)
        self.yamls.append(tenantvalidator_vwc_yaml_file)

    def update_replace_yaml(self):
        # update yaml substitution
        with open(self.dfile('cert')) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{tenantvalidator-csr-data}"] = base64.b64encode(data_bytes)

    def genservicecert(self):
        Log.info(os.linesep + "Generating Tenant Validator Service Cert...", stdout=True)
        Log.info("Generating new self-signed cert...")
        os.chdir(self.MYDIR)
        if not os.path.exists('services'):
            os.mkdir('services')
        if not os.path.exists(self.dfile('key')):
            self.openssl('genrsa', '-out', self.dfile('key'), str(Constants.KEY_SIZE))

        config = open(self.dfile('config'), 'w')
        config.write(Constants.OPENSSL_CONFIG_TEMPLATE % {'service': 'tenant-validator-svc',
                                                          'namespace': 'hpe-system'})
        config.close()
        self.openssl('req', '-new', '-key', self.dfile('key'), '-out', self.dfile('cert'),
                     '-config', self.dfile('config'))
        return True

    def genk8csr(self):
        # clean-up any previously created CSR for our service. Ignore errors if not present.
        uninstallable_yaml_types = ["tenantvalidator_csr_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # create new csr
        installable_yaml_types = ["tenantvalidator_csr_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=False)

        # approve and fetch the signed certificate/pkg/k8client
        Log.info(os.linesep + "Approving the Tenant Validator Service CSR...", True)
        if self.run_kubectl_certificate("approve tenant-validator-svc.hpe-system"):
            Log.info(os.linesep + "Approved the Tenant Validator Service CSR.")
            # this is to try and avoid the failures we've been seeing, perhaps time related
            # verify CSR has been created
            for x in range(3):
                encoded_server_cert = self.run_kubectl_get("csr tenant-validator-svc.hpe-system -o"
                                                           "jsonpath={.status.certificate}")
                if not encoded_server_cert:
                    Log.error("After approving the Tenant Validator Service CSR, the signed certificate did not "
                              "appear on the resource.")
                    return False
                elif encoded_server_cert == "<no response>":
                    Log.info("After approving the Tenant Validator Service CSR, was not able to get a response "
                             "back from the API server for it.  Attempt " + str((x+1)) + " of 3", True)
                    time.sleep(2)
            if not encoded_server_cert:
                Log.error("After approving the Tenant Validator Service CSR, the signed certificate did not "
                          "appear on the resource.")
                return False
            elif encoded_server_cert == "<no response>":
                Log.info("After approving the Tenant Validator Service CSR, was not able to get a response "
                         "back from the API server for it in all 3 attempts")
            else:
                Log.info("Verified the Tenant Validator Service CSR was signed.")
                decoded_cert = base64.b64decode(encoded_server_cert + "========")  # Jira K8S-1489
                file1 = open(self.dfile('csrcert'), 'wb')
                file1.write(decoded_cert)
                file1.close()
                OperationsBase.replace_dict["{tenantvalidator-servercert-encoded}"] = encoded_server_cert
        return True

    def run_install(self, upgrade_mode=False):
        # CERTIFICATE
        self.genservicecert()
        self.update_replace_yaml()
        # CERTIFICATE SIGNING REQUEST
        self.genk8csr()
        # CERTS SECRET
        Log.info(os.linesep + "Deleting previously created Tenant Validator Service certs secret...")
        self.delete_tenantvalidator_secret()
        Log.info(os.linesep + "Creating Tenant Validator Service Certs Secret ...", True)
        if self.create_tenantvalidator_secret(self.dfile('key'), self.dfile('csrcert')):
            Log.info("Created Tenant Validator Service certs secret.")

        uninstallable_yaml_types = ["tenantvalidator_deployemt_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        installable_yaml_types = ["tenantvalidator_components", "tenantvalidator_deployemt_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

        return True

    def run_uninstall(self):
        uninstallable_yaml_types = ["tenantvalidator_components", "tenantvalidator_csr_component",
                                    "tenantvalidator_deployemt_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # SECRET
        Log.info(os.linesep + "Deleting Tenant Validator Service certs Secret...", True)
        self.delete_tenantvalidator_secret()
        Log.info("Deleted Tenant Validator Service certs Secret.")
        return True

    def create_tenantvalidator_secret(self, key_file, cert_file):
        cmd = 'kubectl create secret generic tenant-validator-certs -n hpe-system ' \
              '--from-file=key.pem={0} ' \
              '--from-file=cert.pem={1} '.format(key_file, cert_file)
        return self._run(cmd)

    def delete_tenantvalidator_secret(self):
        cmd = 'kubectl delete secret tenant-validator-certs -n hpe-system --ignore-not-found'
        return self._run(cmd)

    # Helper used to put together filenames for certs
    @staticmethod
    def dfile(ext):
        return os.path.join('services', '%s.%s' % ('tenant-validator-svc', ext))

    @staticmethod
    def openssl(*args):
        cmdline = [Constants.OPENSSL] + list(args)
        fnull = open(os.devnull, 'w')
        subprocess.check_call(cmdline, stdout=fnull, stderr=subprocess.STDOUT)
