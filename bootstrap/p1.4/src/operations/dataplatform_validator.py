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
#  the DataPlatform  infrastructure
#

class DataPlatformValidator(OperationsBase):
    MYDIR = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):
        super(DataPlatformValidator, self).__init__()
        self.dataplatform_dir = os.path.abspath(os.path.join(self.prereq_dir, "system-dataplatform-validator"))
        if not os.path.exists(self.dataplatform_dir):
            raise NotFoundException(self.dataplatform_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.dataplatform_dir, "datavalid-csr.yaml")
        dataplatformvalidator_csr_yaml_file = YamlFile("dataplatformvalidator-csr", "Data Platform Validator Service CSR", file_name, "dataplatformvalidator_csr_component", True, True)
        self.yamls.append(dataplatformvalidator_csr_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-sa.yaml")
        dataplatformvalidator_sa_yaml_file = YamlFile("dataplatformvalidator-sa", "Data Platform Validator Service Account", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_sa_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-cr.yaml")
        dataplatformvalidator_cr_yaml_file = YamlFile("dataplatformvalidator-cr", "Data Platform Validator Cluster Role", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_cr_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-crb.yaml")
        dataplatformvalidator_crb_yaml_file = YamlFile("dataplatformvalidator-crb", "Data Platform Validator Cluster Role Binding", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_crb_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-svc.yaml")
        dataplatformvalidator_service_yaml_file = YamlFile("dataplatformvalidator-service", "Data Platform Validator Service", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_service_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-mwhconfig.yaml")
        dataplatformvalidator_mwc_yaml_file = YamlFile("dataplatformvalidator-mwc", "Data Platform Validator Mutating Admission Controller", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_mwc_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-vwhconfig.yaml")
        dataplatformvalidator_vwc_yaml_file = YamlFile("dataplatformvalidator-vwc", "Data Platform Validator Validating Admission Controller", file_name, "dataplatformvalidator_components", True)
        self.yamls.append(dataplatformvalidator_vwc_yaml_file)

        file_name = self.check_exists(self.dataplatform_dir, "datavalid-deploy.yaml")
        dataplatformvalidator_deployment_yaml_file = YamlFile("dataplatformvalidator-deployment", "Data Platform Validator Deployment", file_name, "dataplatformvalidator_deployemt_component", True, True)
        self.yamls.append(dataplatformvalidator_deployment_yaml_file)

    def update_replace_yaml(self):
        # update yaml substitution
        with open(self.dfile('cert')) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{dataplatformvalidator-csr-data}"] = base64.b64encode(data_bytes)

    def genservicecert(self):
        Log.info(os.linesep + "Generating DataPlatform Validator Service Cert...", stdout=True)
        Log.info("Generating new self-signed cert...")
        os.chdir(self.MYDIR)
        if not os.path.exists('services'):
            os.mkdir('services')
        if not os.path.exists(self.dfile('key')):
            self.openssl('genrsa', '-out', self.dfile('key'), str(Constants.KEY_SIZE))

        config = open(self.dfile('config'), 'w')
        config.write(Constants.OPENSSL_CONFIG_TEMPLATE % {'service': 'dataplatform-validator-svc',
                                                          'namespace': 'hpe-system'})
        config.close()
        self.openssl('req', '-new', '-key', self.dfile('key'), '-out', self.dfile('cert'),
                     '-config', self.dfile('config'))
        return True

    def genk8csr(self):
        # clean-up any previously created CSR for our service. Ignore errors if not present.
        uninstallable_yaml_types = ["dataplatformvalidator_csr_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # create new csr
        installable_yaml_types = ["dataplatformvalidator_csr_component"]
        self.install_components(installable_yaml_types=installable_yaml_types)

        # approve and fetch the signed certificatedataplatformvalidator/pkg/k8client
        Log.info(os.linesep + "Approving the DataPlatform Validator Service CSR...", True)
        if self.run_kubectl_certificate("approve dataplatform-validator-svc.hpe-system"):
            Log.info(os.linesep + "Approved the DataPlatform Validator Service CSR.")
            # this is to try and avoid the failures we've been seeing, perhaps time related
            # verify CSR has been created
            for x in range(3):
                encoded_server_cert = self.run_kubectl_get("csr dataplatform-validator-svc.hpe-system -o"
                                                           "jsonpath={.status.certificate}")
                if not encoded_server_cert:
                    Log.error("After approving the DataPlatform Validator Service CSR, the signed certificate did not "
                              "appear on the resource.")
                    return False
                elif encoded_server_cert == "<no response>":
                    Log.info("After approving the DataPlatform Validator Service CSR, was not able to get a response "
                             "back from the API server for it.  Attempt " + str((x+1)) + " of 3", True)
                    time.sleep(2)
            if not encoded_server_cert:
                Log.error("After approving the DataPlatform Validator Service CSR, the signed certificate did not "
                          "appear on the resource.")
                return False
            elif encoded_server_cert == "<no response>":
                Log.info("After approving the DataPlatform Validator Service CSR, was not able to get a response "
                         "back from the API server for it in all 3 attempts")
            else:
                Log.info("Verified the DataPlatform Validator Service CSR was signed.")
                decoded_cert = base64.b64decode(encoded_server_cert + "========") #Jira K8S-1489
                file1 = open(self.dfile('csrcert'), 'wb')
                file1.write(decoded_cert)
                file1.close()
                OperationsBase.replace_dict["{dataplatformvalidator-servercert-encoded}"] = encoded_server_cert
        return True

    def run_install(self, upgrade_mode=False):
        # CERTIFICATE
        self.genservicecert()
        self.update_replace_yaml()
        # CERTIFICATE SIGNING REQUEST
        self.genk8csr()
        # CERTS SECRET
        Log.info(os.linesep + "Deleting previously created DataPlatform Validator Service certs secret...")
        self.delete_dataplatformvalidator_secret()
        Log.info(os.linesep + "Creating DataPlatform Validator Service Certs Secret ...", True)
        if self.create_dataplatformvalidator_secret(self.dfile('key'), self.dfile('csrcert')):
            Log.info("Created DataPlatform Validator Service certs secret.")

        uninstallable_yaml_types = ["dataplatformvalidator_deployemt_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        installable_yaml_types = ["dataplatformvalidator_components", "dataplatformvalidator_deployemt_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

        return True

    def run_uninstall(self):
        uninstallable_yaml_types = ["dataplatformvalidator_components","dataplatformvalidator_csr_component", "dataplatformvalidator_deployemt_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # SECRET
        Log.info(os.linesep + "Deleting DataPlatform Validator Service certs Secret...", True)
        self.delete_dataplatformvalidator_secret()
        Log.info("Deleted DataPlatform Validator Service certs Secret.")
        return True

    def create_dataplatformvalidator_secret(self, key_file, cert_file):
        cmd = 'kubectl create secret generic dataplatform-validator-certs -n hpe-system ' \
              '--from-file=key.pem={0} ' \
              '--from-file=cert.pem={1} '.format(key_file, cert_file)
        return self._run(cmd)

    def delete_dataplatformvalidator_secret(self):
        cmd = 'kubectl delete secret dataplatform-validator-certs -n hpe-system --ignore-not-found'
        return self._run(cmd)

    # Helper used to put together filenames for certs
    @staticmethod
    def dfile(ext):
        return os.path.join('services', '%s.%s' % ('dataplatform-validator-svc', ext))

    @staticmethod
    def openssl(*args):
        cmdline = [Constants.OPENSSL] + list(args)
        fnull = open(os.devnull, 'w')
        subprocess.check_call(cmdline, stdout=fnull, stderr=subprocess.STDOUT)
