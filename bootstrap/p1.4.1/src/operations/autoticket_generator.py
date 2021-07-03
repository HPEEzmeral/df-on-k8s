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
#  the AutoTicketGenerator infrastructure
#  including generating certs for it at install time
#


class AutoTicketGenerator(OperationsBase):
    MYDIR = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):
        super(AutoTicketGenerator, self).__init__()
        self.autoticket_dir = os.path.abspath(os.path.join(self.prereq_dir, "system-autoticket"))
        if not os.path.exists(self.autoticket_dir):
            raise NotFoundException(self.autoticket_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.autoticket_dir, "autoticket-csr.yaml")
        autoticket_csr_yaml_file = YamlFile("autoticket-csr", "Auto Ticket Generator Service CSR", file_name, "autoticket_csr_component", ignore_not_found=True)
        self.yamls.append(autoticket_csr_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-sa.yaml")
        autoticket_sa_yaml_file = YamlFile("autoticket-sa", "Auto Ticket Generator Service Account", file_name, "autoticket_components")
        self.yamls.append(autoticket_sa_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-cr.yaml")
        autoticket_cr_yaml_file = YamlFile("autoticket-cr", "Auto Ticket Generator Cluster Role", file_name, "autoticket_components")
        self.yamls.append(autoticket_cr_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-crb.yaml")
        autoticket_crb_yaml_file = YamlFile("autoticket-crb", "Auto Ticket Generator Cluster Role Binding", file_name, "autoticket_components")
        self.yamls.append(autoticket_crb_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-svc.yaml")
        autoticket_svc_yaml_file = YamlFile("autoticket-service", "Auto Ticket Generator Service", file_name, "autoticket_components")
        self.yamls.append(autoticket_svc_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-mwhconfig.yaml")
        autoticket_mwc_yaml_file = YamlFile("autoticket-mwc", "Auto Ticket Generator Mutating Admission Controller", file_name, "autoticket_components")
        self.yamls.append(autoticket_mwc_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-vwhconfig.yaml")
        autoticket_vwc_yaml_file = YamlFile("autoticket-vwc", "Auto Ticket Generator Validating Admission Controller", file_name, "autoticket_components")
        self.yamls.append(autoticket_vwc_yaml_file)

        file_name = self.check_exists(self.autoticket_dir, "autoticket-deploy.yaml")
        autoticket_deployment_yaml_file = YamlFile("autoticket-deployment", "Auto Ticket Generator Deployment", file_name, "autoticket_deployment_component", ignore_not_found=True)
        self.yamls.append(autoticket_deployment_yaml_file)

    def update_replace_yaml(self):
        # update yaml substitution
        with open(self.dfile('cert')) as readfile:
            file_contents = readfile.read()
        data_bytes = file_contents.encode("utf-8")
        OperationsBase.replace_dict["{autoticket-csr-data}"] = base64.b64encode(data_bytes)

    def genservicecert(self):
        Log.info(os.linesep + "Generating Auto Ticket Generator Service Cert...", stdout=True)
        Log.info("Generating new self-signed cert...")
        os.chdir(self.MYDIR)
        if not os.path.exists('services'):
            os.mkdir('services')
        if not os.path.exists(self.dfile('key')):
            self.openssl('genrsa', '-out', self.dfile('key'), str(Constants.KEY_SIZE))

        config = open(self.dfile('config'), 'w')
        config.write(Constants.OPENSSL_CONFIG_TEMPLATE % {'service': 'autoticket-generator-svc',
                                                          'namespace': 'hpe-system'})
        config.close()
        self.openssl('req', '-new', '-key', self.dfile('key'), '-out', self.dfile('cert'),
                     '-config', self.dfile('config'))
        return True

    def genk8csr(self):
        # clean-up any previously created CSR for our service. Ignore errors if not present.
        encoded_server_cert = None
        uninstallable_yaml_types = ["autoticket_csr_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # create new csr
        installable_yaml_types = ["autoticket_csr_component"]
        self.install_components(installable_yaml_types=installable_yaml_types)

        # approve and fetch the signed certificateautoticket-generator/pkg/k8client
        Log.info(os.linesep + "Approving the Auto Ticket Generator Service CSR...", True)
        if self.run_kubectl_certificate("approve autoticket-generator-svc.hpe-system"):
            Log.info(os.linesep + "Approved the Auto Ticket Generator Service CSR.")
            # this is to try and avoid the failures we've been seeing, perhaps time related
            # verify CSR has been created
            for x in range(3):
                encoded_server_cert = self.run_kubectl_get("csr autoticket-generator-svc.hpe-system -o"
                                                           "jsonpath={.status.certificate}")
                if not encoded_server_cert:
                    Log.error("After approving the Auto Ticket Generator Service CSR, the signed certificate did not "
                              "appear on the resource.")
                    return False
                elif encoded_server_cert == "<no response>":
                    Log.info("After approving the Auto Ticket Generator Service CSR, was not able to get a response "
                              "back from the API server for it.  Attempt " + str((x+1)) + " of 3", True)
                    time.sleep(2)
            if not encoded_server_cert:
                Log.error("After approving the Auto Ticket Generator Service CSR, the signed certificate did not "
                          "appear on the resource.")
                return False
            elif encoded_server_cert == "<no response>":
                Log.info("After approving the Auto Ticket Generator Service CSR, was not able to get a response "
                         "back from the API server for it in all 3 attempts")
            else:
                Log.info("Verified the Auto Ticket Generator Service CSR was signed.")
                # Jira K8S-1489
                decoded_cert = base64.b64decode(encoded_server_cert + "========")
                file1 = open(self.dfile('csrcert'), 'wb')
                file1.write(decoded_cert)
                file1.close()
                OperationsBase.replace_dict["{autoticket-servercert-encoded}"] = encoded_server_cert
        return True

    def run_install(self, upgrade_mode=False):
        # CERTIFICATE
        self.genservicecert()
        self.update_replace_yaml()
        # CERTIFICATE SIGNING REQUEST
        self.genk8csr()
        # CERTS SECRET
        Log.info(os.linesep + "Deleting previously created Auto Ticket Generator Service certs secret...")
        self.delete_autoticket_secret()
        Log.info(os.linesep + "Creating Auto Ticket Generator Service Certs Secret ...", True)
        if self.create_autoticket_secret(self.dfile('key'), self.dfile('csrcert')):
            Log.info("Created Auto Ticket Generator Service certs secret.")

        uninstallable_yaml_types = ["autoticket_deployment_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        installable_yaml_types = ["autoticket_components", "autoticket_deployment_component"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

        return True

    def run_uninstall(self):
        uninstallable_yaml_types = ["autoticket_components", "autoticket_csr_component", "autoticket_deployment_component"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)

        # SECRET
        Log.info(os.linesep + "Deleting Auto Ticket Generator Service certs Secret...", True)
        self.delete_autoticket_secret()
        Log.info("Deleted Auto Ticket Generator Service certs Secret.")
        return True

    def create_autoticket_secret(self, key_file, cert_file):
        cmd = 'kubectl create secret generic autoticket-generator-certs -n hpe-system ' \
              '--from-file=key.pem={0} ' \
              '--from-file=cert.pem={1} '.format(key_file, cert_file)
        return self._run(cmd)

    def delete_autoticket_secret(self):
        cmd = 'kubectl delete secret autoticket-generator-certs -n hpe-system --ignore-not-found'
        return self._run(cmd)

    # Helper used to put together filenames for certs
    @staticmethod
    def dfile(ext):
        return os.path.join('services', '%s.%s' % ('autoticket-generator-svc', ext))

    @staticmethod
    def openssl(*args):
        cmdline = [Constants.OPENSSL] + list(args)
        fnull = open(os.devnull, 'w')
        subprocess.check_call(cmdline, stdout=fnull, stderr=subprocess.STDOUT)
