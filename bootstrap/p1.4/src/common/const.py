
class Constants(object):
    LOGGER_CONF = "common/mapr_conf/logger.yml"
    USERNAME = "mapr"
    PASSWORD = "mapr"
    GROUPNAME = "mapr"
    USERID = 5000
    GROUPID = 5000
    ADMIN_USERNAME = "custadmin"
    ADMIN_GROUPNAME = "custadmin"
    ADMIN_USERID = 7000
    ADMIN_GROUPID = 7000
    ADMIN_PASS = "mapr"
    MYSQL_USER = "admin"
    MYSQL_PASS = "mapr"
    LDAPADMIN_USER = "admin"
    LDAPADMIN_PASS = "mapr"
    LDAPBIND_USER = "readonly"
    LDAPBIND_PASS = "mapr"
    EXAMPLE_LDAP_NAMESPACE = "hpe-ldap"
    CSI_REPO = "quay.io/k8scsi"
    KDF_REPO = "quay.io/maprtech" #registry.hub.docker.com/maprtech
    KUBEFLOW_REPO = "gcr.io/mapr-252711/kf-ecp-5.3.0"
    OPERATOR_REPO = "gcr.io/mapr-252711"
    KUBELET_DIR = "/var/lib/kubelet"
    ECP_KUBELET_DIR = "/var/lib/docker/kubelet"
    LOCAL_PATH_PROVISIONER_REPO= ""
    KFCTL_HSP_ISTIO_REPO = ""
    BUSYBOX_REPO = ""

    def enum(**named_values):
        return type('Enum', (), named_values)

    AUTH_TYPES = enum(CUSTOM_LDAP='customLDAP', RAW_LINUX_USERS='rawLinuxUsers', EXAMPLE_LDAP='exampleLDAP')
# OPEN SSL
    OPENSSL = '/usr/bin/openssl'
    KEY_SIZE = 1024
    DAYS = 3650
    CA_CERT = 'ca.cert'
    CA_KEY = 'ca.key'
    # http://www.openssl.org/docs/apps/openssl.html#PASS_PHRASE_ARGUMENTS
    X509_EXTRA_ARGS = ()

    OPENSSL_CONFIG_TEMPLATE = """
prompt = no
distinguished_name = req_distinguished_name
req_extensions = v3_req

[ req_distinguished_name ]
C                      = US
ST                     = CO
L                      = Fort Collins
O                      = HPE
OU                     = HCP
CN                     = %(service)s
emailAddress           = support@hpe.com
[ v3_req ]
# Extensions to add to a certificate request
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[ alt_names ]
DNS.1 = %(service)s
DNS.2 = %(service)s.%(namespace)s
DNS.3 = %(service)s.%(namespace)s.svc
"""
