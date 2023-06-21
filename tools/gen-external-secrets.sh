#!/usr/bin/env bash

# gen-external-secrets for core 6.1, 6.2, 7.0, 7.1, 7.2, 7.3, 7.4

ECHOE="echo -e"

# return codes
NO=0
YES=1
INFO=0
WARN=-1
ERROR=1

MAPR_HOME=${MAPR_HOME:-"/opt/mapr"}
CONFDIR="$MAPR_HOME/conf"
CA_CONFDIR=$CONFDIR/"ca"
PROMPT_SILENT=$NO
SECURE_CLUSTER="false"
CLUSTER_NAME="my.cluster.com"

USERNAME="mapr"
PASSWORD="mapr"
GROUP_NAME="mapr"
USER_ID="5000"
GROUP_ID="5000"
SERVER_TICKET="TICKETSTRING"
CLDB_NODES="cldb-2.cldb-svc.mycluster.svc.cluster.local,cldb-1.cldb-svc.mycluster.svc.cluster.local,cldb-0.cldb-svc.mycluster.svc.cluster.local"
ZK_NODES="zk-0.zk-svc.mycluster.svc.cluster.local:5181,zk-1.zk-svc.mycluster.svc.cluster.local:5181,zk-2.zk-svc.mycluster.svc.cluster.local:5181"
KEYSTORE="KEYSTORESTRING"
TRUSTSTORE="TRUSTSTORESTRING"
EXTERNAL_SECRETS_NAMESPACE="hpe-externalclusterinfo"
USER_SECRET_NAME="mapr-user-secrets"
SERVER_SECRET_NAME="mapr-server-secrets"
SERVER_CONFIGMAP_NAME="mapr-external-cm"
CLIENT_SECRET_NAME="mapr-client-secrets"
HIVESITE_CONFIGMAP_NAME="mapr-hivesite-cm"
OUTPUT_FILE="mapr-external-secrets.yaml"
SSLSERVERXML_FILE=$CONFDIR/"ssl-server.xml"
SSLCLIENTXML_FILE=$CONFDIR/"ssl-client.xml"
KEYCREDS_FILE=$CONFDIR/"maprkeycreds.jceks"
TRUSTCREDS_FILE=$CONFDIR/"maprtrustcreds.jceks"
PUBLIC_CRT_FILE=$CONFDIR/"public.crt"
PRIVATE_KEY_FILE=$CONFDIR/"private.key"
CHAIN_CA_CERT_PEM_FILE=$CA_CONFDIR/"chain-ca.pem"
ROOT_CA_CERT_PEM_FILE=$CA_CONFDIR/"root-ca.pem"
SIGNING_CA_CERT_PEM_FILE=$CA_CONFDIR/"signing-ca.pem"

# Output an error, warning or regular message
msg() {
  msg_format "$1" $2
}

msg_prefix() {
  ts=`date "+%Y/%m/%d %H:%M:%S"`
  prefix="$ts $CURRENT_FILE"
}

# Print each word according to the screen size
msg_format() {
    local length=0
    local width=""
    local words=$1

    width=$(tput cols)
    width=${width:-80}
    for word in $words; do
        length=$(($length + ${#word} + 1))
        if [ $length -gt $width ]; then
            $ECHOE "\n$word \c"
            length=$((${#word} + 1))
        else
            $ECHOE "$word \c"
        fi
    done
}

msg_err() {
  msg_prefix
  msg_format "$prefix: [ERROR] $1"
}

prompt() {
    local query=$1
    local default=${2:-""}

    shift 2
    if [ $PROMPT_SILENT -eq $YES ]; then
        if [ -z "$default" ]; then
            msg_err "no default value available"
        else
            msg "$query: $default\n" "-"
            ANSWER=$default
            return
        fi
    fi
    unset ANSWER
    # allow SIGINT to interrupt
    trap - SIGINT
    while [ -z "$ANSWER" ]; do
        if [ -z "$default" ]; then
            msg "$query:" "-"
        else
            msg "$query [$default]:" "-"
        fi
        if [ "$1" = "-s" ] && [ -z "$BASH" ]; then
            trap 'stty echo' EXIT
            stty -echo
            read ANSWER
            stty echo
            trap - EXIT
        else
            read $* ANSWER
        fi
        if [ "$ANSWER" = "q!" ]; then
            exit 1
        elif [ -z "$ANSWER" ] && [ -n "$default" ]; then
            ANSWER=$default
        fi
        [ "$1" = "-s" ] && echo
    done
    trap '' SIGINT
}

prompt_boolean() {
    unset ANSWER
    while [ -z "$ANSWER" ]; do
        prompt "$1 (y/n)" ${2:-y}
        case "$ANSWER" in
        n*|N*) ANSWER=$NO; break ;;
        y*|Y*) ANSWER=$YES; break ;;
        *) unset ANSWER ;;
        esac
    done
}

msg_bold() {
    tput bold
    msg_format "$1"
    tput sgr0
}

parse_cluster() {
  SECURE_CLUSTER=`echo $CLUSTER_STRING | cut --complement -d "=" -f 1 | cut -d " " -f 1`
  CLUSTER_NAME=`echo $CLUSTER_STRING | cut -d " " -f 1`
  CLUSTER_ID=`cat $CONFDIR/clusterid`
  CLUSTER_ID_BASE64=`cat $CONFDIR/clusterid | base64 -w 0`
  echo "Setting cluster name to: $CLUSTER_NAME..."
}

get_userinfo() {
  id $USERNAME
  rc="$?"
  if [ $rc == 0 ]; then
    GROUP_NAME=`groups $USERNAME | cut -d ' ' -f 1`
    USER_ID=`id -u $USERNAME`
    GROUP_ID=`id -g $USERNAME | cut -d ' ' -f 1`
  else
    echo "Error - Username not found. Please enter a valid user."
    exit 1
  fi
}

create_user_secret() {
  USER_B64=`printf $USERNAME | base64`
  PASSWORD_B64=`printf $PASSWORD | base64`
  GROUP_B64=`printf $GROUP_NAME | base64`
  UID_B64=`printf $USER_ID | base64`
  GID_B64=`printf $GROUP_ID | base64`

  UNSECURE_SECRETS_FILE_HEADER=$(cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: $USER_SECRET_NAME
  namespace: $EXTERNAL_SECRETS_NAMESPACE
  annotations:
    mapr.com/externalcluster: "$CLUSTER_NAME"
type: Opaque
EOF
)

  if [ $IS_KUBERNETES -eq $NO ]; then
    UNSECURE_SECRETS_FILE_DATA=$(cat <<EOF

data:
  MAPR_USER:     "$USER_B64"
  MAPR_PASSWORD: "$PASSWORD_B64"
  MAPR_GROUP:    "$GROUP_B64"
  MAPR_UID:      "$UID_B64"
  MAPR_GID:      "$GID_B64"
EOF
)
  else
    UNSECURE_SECRETS_FILE_DATA=$(cat /tmp/user-secrets.yaml)
  fi
SECRETS_FILE="$UNSECURE_SECRETS_FILE_HEADER$UNSECURE_SECRETS_FILE_DATA"
}

create_secure_secret() {
  SERVER_TICKET=`cat $CONFDIR/maprserverticket | base64 -w 0`
  USER_TICKET=`cat $CONFDIR/mapruserticket | base64 -w 0`

  local truststore_file=`xmllint --xpath '/configuration/property[contains(name,"ssl.server.truststore.location")]/value/text()' $SSLSERVERXML_FILE`
  local truststore_key=`xmllint --xpath '/configuration/property[contains(name,"ssl.server.truststore.password")]/value/text()' $SSLSERVERXML_FILE`
  local keystore_file=`xmllint --xpath '/configuration/property[contains(name,"ssl.server.keystore.location")]/value/text()' $SSLSERVERXML_FILE`
  local keystore_key=`xmllint --xpath '/configuration/property[contains(name,"ssl.server.keystore.password")]/value/text()' $SSLSERVERXML_FILE`

  KEYSTORE=`cat $keystore_file | base64 -w 0`
  KEYSTORE_KEY=`echo $keystore_key | base64 -w 0`

  # Check if keystore pem exists?
  if [ -f $CONFDIR/ssl_keystore.pem ]; then
    #crack it open
    KEYSTORE_PEM=`cat $CONFDIR/ssl_keystore.pem | base64 -w 0`
  fi
  # Check if keystpre p12 exists?
  if [ -f $CONFDIR/ssl_keystore.p12 ]; then
    KEYSTORE_P12=`cat $CONFDIR/ssl_keystore.p12 | base64 -w 0`
  fi
  TRUSTSTORE=`cat $truststore_file | base64 -w 0`
  TRUSTSTORE_KEY=`echo $keystore_key | base64 -w 0`
  # Check if truststore pem exist?
  if [ -f $CONFDIR/ssl_truststore.pem ]; then
    TRUSTSTORE_PEM=`cat $CONFDIR/ssl_truststore.pem | base64 -w 0`
  fi
  # Check if truststore p12 exists
  if [ -f $CONFDIR/ssl_truststore.p12 ]; then
    TRUSTSTORE_P12=`cat $CONFDIR/ssl_truststore.p12 | base64 -w 0`
  fi
  # Check if ssl-client.xml exists
  if [ -f $SSLCLIENTXML_FILE ]; then
    SSL_CLIENT_XML=`cat $SSLCLIENTXML_FILE | base64 -w 0`
  fi
  # Check if maprkeycreds.jceks exists
  if [ -f $KEYCREDS_FILE ]; then
    KEYSTORE_CREDS=`cat $KEYCREDS_FILE | base64 -w 0`
  fi
   # Check if maprtrustcreds.jceks exists
  if [ -f $TRUSTCREDS_FILE ]; then
    TRUSTSTORE_CREDS=`cat $TRUSTCREDS_FILE | base64 -w 0`
  fi
  # Check if ssl-server.xml exists
  if [ -f $SSLSERVERXML_FILE ]; then
    SSL_SERVER_XML=`cat $SSLSERVERXML_FILE | base64 -w 0`
  fi
  # Check if public.crt exists
  if [ -f $PUBLIC_CRT_FILE ]; then
    PUBLIC_CRT=`cat $PUBLIC_CRT_FILE | base64 -w 0`
  fi
  # Check if private.key exists
  if [ -f $PRIVATE_KEY_FILE ]; then
    PRIVATE_KEY=`cat $PRIVATE_KEY_FILE | base64 -w 0`
  fi
  # Check if chain-ca.pem exists
  if [ -f $CHAIN_CA_CERT_PEM_FILE ]; then
    CHAIN_CA_CERT_PEM=`cat $CHAIN_CA_CERT_PEM_FILE | base64 -w 0`
  fi
  # Check if root-ca.pem exists
  if [ -f $ROOT_CA_CERT_PEM_FILE ]; then
    ROOT_CA_CERT_PEM=`cat $ROOT_CA_CERT_PEM_FILE | base64 -w 0`
  fi
  # Check if signing-ca.pem exists
  if [ -f $SIGNING_CA_CERT_PEM_FILE ]; then
    SIGNING_CA_CERT_PEM=`cat $SIGNING_CA_CERT_PEM_FILE | base64 -w 0`
  fi

  SECURE_SERVER_SECRETS_FILE_HEADER=$(cat <<EOF

---
apiVersion: v1
kind: Secret
metadata:
  name: $SERVER_SECRET_NAME
  namespace: $EXTERNAL_SECRETS_NAMESPACE
  annotations:
    mapr.com/externalcluster: "$CLUSTER_NAME"
type: Opaque
EOF
)
  if [ $IS_KUBERNETES -eq $NO ]; then
    SECURE_SERVER_SECRETS_FILE_DATA=$(cat <<EOF

data:
  clusterid: >-
    $CLUSTER_ID_BASE64
  maprmetricsticket: >-
    $USER_TICKET
  maprserverticket: >-
    $SERVER_TICKET
  ssl_keystore: >-
    $KEYSTORE
  ssl_keystore.p12: >-
    $KEYSTORE_P12
  ssl_keystore.pem: >-
    $KEYSTORE_PEM
  ssl_keystore_key: >-
    $KEYSTORE_KEY
  ssl-server.xml: >-
    $SSL_SERVER_XML
  maprkeycreds.jceks: >-
    $KEYSTORE_CREDS
  private.key: >-
    $PRIVATE_KEY
EOF
)
  else
    SECURE_SERVER_SECRETS_FILE_DATA=$(cat /tmp/server-secrets.yaml)
  fi

  SECURE_CLIENT_SECRETS_FILE_HEADER=$(cat <<EOF

---
apiVersion: v1
kind: Secret
metadata:
  name: $CLIENT_SECRET_NAME
  namespace: $EXTERNAL_SECRETS_NAMESPACE
  annotations:
    mapr.com/externalcluster: "$CLUSTER_NAME"
type: Opaque
EOF
)
  if [ $IS_KUBERNETES -eq $NO ]; then
    SECURE_CLIENT_SECRETS_FILE_DATA=$(cat <<EOF

data:
  ssl_truststore: >-
    $TRUSTSTORE
  ssl_truststore.p12: >-
    $TRUSTSTORE_P12
  ssl_truststore.pem: >-
    $TRUSTSTORE_PEM
  ssl_truststore_key: >-
    $TRUSTSTORE_KEY
  ssl-client.xml: >-
    $SSL_CLIENT_XML
  maprtrustcreds.jceks: >-
    $TRUSTSTORE_CREDS
  public.crt: >-
    $PUBLIC_CRT
  root-ca.pem: >-
    $ROOT_CA_CERT_PEM
  signing-ca.pem: >-
    $SIGNING_CA_CERT_PEM
  chain-ca.pem: >-
    $CHAIN_CA_CERT_PEM
EOF
)
  else
    SECURE_CLIENT_SECRETS_FILE_DATA=$(cat /tmp/client-secrets.yaml)
  fi

SECRETS_FILE="$UNSECURE_SECRETS_FILE_HEADER$UNSECURE_SECRETS_FILE_DATA$SECURE_SERVER_SECRETS_FILE_HEADER$SECURE_SERVER_SECRETS_FILE_DATA$SECURE_CLIENT_SECRETS_FILE_HEADER$SECURE_CLIENT_SECRETS_FILE_DATA"
}

get_maprcli_nodes() {
  local svc_name=$1
  maprcli node list -filter [svc==$svc_name] -columns ip > nodes
  cat nodes
  if [ -s nodes ]; then
    NODES=`cat nodes | tail -n+2  | awk -vORS=, '{ print $1 }'  | sed 's/,$/\n/'`
  else
    echo "Cannot locate $svc_name nodes"
  fi
  rm -rf nodes
}

create_node_list() {
  local svc_name=$1
  NODES=""
  echo "Querying $svc_name nodes..."
  if [ $IS_KUBERNETES -eq $NO ]; then
    case "$svc_name" in
              cldb)
                NODES=`maprcli node listcldbs | sed -n -e '2{p;q}' | tr -d '\040\011\012\015'`
                echo $NODES
                return 0
                ;;
          zookeeper)
                NODES=`maprcli node listzookeepers | sed -n -e '2{p;q}' | tr -d '\040\011\012\015'`
                echo $NODES
                return 0
                ;;
    esac
    get_maprcli_nodes $svc_name
    return 0
  else
    case "$svc_name" in
              cldb)
                NODES=$MAPR_CLDB_HOSTS
                echo $NODES
                return 0
                ;;
          zookeeper)
                NODES=$MAPR_ZK_HOSTS
                echo $NODES
                return 0
                ;;
          hivemeta)
                NODES=$MAPR_HIVEM_HOSTS
                echo $NODES
                return 0
                ;;
          opentsdb)
                NODES=$MAPR_TSDB_HOSTS
                echo $NODES
                return 0
                ;;
                 *)
                get_maprcli_nodes $svc_name
                ;;
    esac
  fi
  return 0
}

create_server_configmap() {
  DISABLE_SECURITY="true"
  if [ $SECURE_CLUSTER == "true" ]; then
    DISABLE_SECURITY="false"
  fi
  create_node_list cldb
  CLDB_NODES=$NODES
  create_node_list zookeeper
  ZK_NODES=$NODES
  create_node_list elasticsearch
  ES_NODES=$NODES
  create_node_list opentsdb
  TSDB_NODES=$NODES
  create_node_list hivemeta
  HIVEMETA_NODES=$NODES
  create_node_list mastgateway
  MASTGATEWAY_NODES=$NODES
  create_node_list gateway
  MAPRGATEWAY_NODES=$NODES
  create_node_list data-access-gateway
  DAG_NODES=$NODES
  create_node_list nfs
  NFS_NODES=$NODES
  create_node_list nfs4
  NFS4_NODES=$NODES
  create_node_list objectstore-client
  OBJECTSTORE_NODES=$NODES
  create_node_list kafka-rest
  KAFKAREST_NODES=$NODES
  create_node_list fileserver
  MFS_NODES=$NODES
  create_node_list hoststats
  HOSTSTATS_NODES=$NODES
  create_node_list apiserver
  APISERVER_NODES=$NODES
  create_node_list nodemanager
  NODEMANAGER_NODES=$NODES
  create_node_list resourcemanager
  RESOURCEMANAGER_NODES=$NODES
  create_node_list hbase
  HBASE_NODES=$NODES

  SERVER_CONFIGMAP_HEADER=$(cat <<EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: $SERVER_CONFIGMAP_NAME
  namespace: $EXTERNAL_SECRETS_NAMESPACE
EOF
)

  if [ $IS_KUBERNETES -eq $NO ]; then
    SERVER_CONFIGMAP_DATA=$(cat <<EOF

data:
  MAPR_HOME: >-
    $MAPR_HOME
  clusterid: >-
    $CLUSTER_ID
  MAPR_CLUSTER: >-
    $CLUSTER_NAME
  clustername: >-
    $CLUSTER_NAME
  SECURE_CLUSTER: >-
    $SECURE_CLUSTER
  disableSecurity: >-
    $DISABLE_SECURITY
  cldbLocations: >-
    $CLDB_NODES
  MAPR_CLDB_HOSTS: >-
    $CLDB_NODES
  zkLocations: >-
    $ZK_NODES
  MAPR_ZK_HOSTS: >-
    $ZK_NODES
  esLocations: >-
    $ES_NODES
  tsdbLocations: >-
    $TSDB_NODES
  hivemetaLocations: >-
    $HIVEMETA_NODES
  mastgatewayLocations: >-
    $MASTGATEWAY_NODES
  maprgatewayLocations: >-
    $MAPRGATEWAY_NODES
  dagLocations: >-
    $DAG_NODES
  nfsLocations: >-
    $NFS_NODES
  nfs4Locations: >-
    $NFS4_NODES
  objectstoreLocations: >-
    $OBJECTSTORE_NODES
  kafkarestLocations: >-
    $KAFKAREST_NODES
  mfsLocations: >-
    $MFS_NODES
  hoststatsLocations: >-
    $HOSTSTATS_NODES
  apiserverLocations: >-
    $APISERVER_NODES
  nodemanagerLocations: >-
    $NODEMANAGER_NODES
  resourcemanagerLocations: >-
    $RESOURCEMANAGER_NODES
  hbaseLocations: >-
    $HBASE_NODES
EOF
)
  else
    SERVER_CONFIGMAP_DATA=$(cat /tmp/external-cm.yaml)
  fi

  echo "$SERVER_CONFIGMAP_HEADER$SERVER_CONFIGMAP_DATA" >> $OUTPUT_FILE
  # Fail if unable to get cldb and ZK information using maprcli
  if [[ -z $CLDB_NODES || -z $ZK_NODES ]]; then
      echo "Failed to retrieve Cldb or Zookeeper info. Exiting.."
      exit 1
  fi
}

create_hivesite_configmap() {
  if [ $IS_KUBERNETES -eq $NO ]; then
    HIVE_DIR=$MAPR_HOME/hive
    if [ -d $HIVE_DIR ]; then
      HIVE_VERSION=$(cat $HIVE_DIR/hiveversion)
      HIVE_HOME=$HIVE_DIR/hive-$HIVE_VERSION
      HIVESITE_FILE=$HIVE_HOME/conf/hive-site.xml
      if [ -f $HIVESITE_FILE ]; then
          # hive-site.xml
          hivesitexml=`cat $HIVESITE_FILE`
      else
        echo "Hive-site.xml not found, skipping hive-site configmap.."
        return 0
      fi
    else
      echo "Hive directory $HIVE_DIR not found, Skipping hive-site confimap.."
      return 0
    fi
  else
    DATAPLATFORM=$(cat /tmp/dataplatform.namespace)
    IS_KUBERNETES_HIVE=$(kubectl get pods -n $DATAPLATFORM | grep hivemeta | grep -v NAME | wc -l)
    if [ $IS_KUBERNETES_HIVE -eq 0 ]; then
      echo "There is no hivemeta pod, Skipping hive-site confimap.."
      return 0
    fi
  fi

  prompt "Please provide the hivesite configmap name:" $HIVESITE_CONFIGMAP_NAME
  HIVESITE_CONFIGMAP_NAME=$ANSWER
  # Hive is installed.  Create configmap
  HIVE_SITE_CONFIGMAP_HEADER=$(cat <<EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: $HIVESITE_CONFIGMAP_NAME
  namespace: $EXTERNAL_SECRETS_NAMESPACE
  annotations:
    mapr.com/externalcluster: "$CLUSTER_NAME"
EOF
  )

  if [ $IS_KUBERNETES -eq $NO ]; then
    HIVE_SITE_CONFIGMAP_DATA=$(cat <<EOF

data:
  hive-site.xml: |
    `echo -n $hivesitexml`
EOF
    )
  else
    HIVE_SITE_CONFIGMAP_DATA=$(cat /tmp/hivesite-cm.yaml)
  fi
  echo "$HIVE_SITE_CONFIGMAP_HEADER$HIVE_SITE_CONFIGMAP_DATA" >> $OUTPUT_FILE

}

prompt "Please provide output filename:" $OUTPUT_FILE
OUTPUT_FILE=$ANSWER
prompt "Please provide the MapR username:" $USERNAME
USERNAME=$ANSWER
prompt "Please provide $USERNAME's password:" $PASSWORD
PASSWORD=$ANSWER
if [ -e $CONFDIR/mapr-clusters.conf ]; then
  echo "$CONFDIR/mapr-clusters.conf: "
  cat $CONFDIR/mapr-clusters.conf
  CLUSTER_STRING=`cat $CONFDIR/mapr-clusters.conf`
  parse_cluster
else
  echo "Error - $CONFDIR/mapr-clusters.conf not found. Please run this on a mapr node."
  exit 1
fi
prompt_boolean "Is this a Kubernetes Storage Node?" n
IS_KUBERNETES=$ANSWER
prompt "Please provide the server configmap name:" $SERVER_CONFIGMAP_NAME
SERVER_CONFIGMAP_NAME=$ANSWER
prompt "Please provide the user secret name:" $USER_SECRET_NAME
USER_SECRET_NAME=$ANSWER
if [ $SECURE_CLUSTER == "true" ]; then
  prompt "Please provide the server secret name:" $SERVER_SECRET_NAME
  SERVER_SECRET_NAME=$ANSWER
  prompt "Please provide the client secret name:" $CLIENT_SECRET_NAME
  CLIENT_SECRET_NAME=$ANSWER
  if [ -e $CONFDIR/maprserverticket ]; then
    TICKET_STRING=`maprlogin print -ticketfile $CONFDIR/maprserverticket`
    get_userinfo
    create_user_secret
    echo "Attempting to create info for secure cluster..."
    create_secure_secret
  else
    echo "Error - $CONFDIR/maprserverticket not found. Please run this on a node with a server ticket."
    exit 1
  fi
else
  echo "Attempting to create info for unsecure cluster..."
  get_userinfo
  create_user_secret
fi
echo "$SECRETS_FILE" >$OUTPUT_FILE
create_server_configmap
create_hivesite_configmap
echo ""
echo "The external information generated for this cluster are available at: $OUTPUT_FILE"
echo "Please copy them to a machine where you can run the following command: "
echo "  kubectl apply -f $OUTPUT_FILE"
