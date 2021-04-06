#!/usr/bin/env bash

HSMSETUP_DIR=`dirname $0`
#
# The cluster name is a required argument
#
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <cluster-name>"
  exit 1
fi

if [ -r ${HSMSETUP_DIR}/tools-common.sh ]; then
  . ${HSMSETUP_DIR}/tools-common.sh
fi
CLUSTER_NAME=$1
PWD=`pwd`
echo "Configuring HSM for cluster ${CLUSTER_NAME}"
mkdir -p ${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME}/tokens
docker pull gcr.io/mapr-252711/hsmsetup-6.2.0:latest
/bin/rm -f /tmp/hsmsetup_dockerid
docker run --cidfile /tmp/hsmsetup_dockerid -i -t -v "${PWD}/${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME}":/opt/mapr/hsmsetup:rw -v "${PWD}/${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME}/tokens":/opt/mapr/conf/tokens --env CLUSTER_NAME="${CLUSTER_NAME}" gcr.io/mapr-252711/hsmsetup-6.2.0:latest /opt/mapr/kubernetes/setup-hsm-docker.sh

STATUS=$?
HSMCONTAINER_ID=`cat /tmp/hsmsetup_dockerid`
echo Removing Docker container $HSMCONTAINER_ID                       
docker rm $HSMCONTAINER_ID

if [ $STATUS -ne 0 ]; then
  echo "Error running Docker container. Exiting"
  exit 1
fi

prompt_boolean "Continue to create HSM secret?" y
CREATE_HSM_SECRET=$ANSWER

if [ $CREATE_HSM_SECRET -eq $NO ]; then
  echo "You can continue running $0 again until you have successfully completed your HSM configuration."
  echo "Your configuration has been saved to ${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME}/tokens. Keep this"
  echo "configuration and your SO PIN in a secure location. You will need the SO PIN to modify the"
  echo "configuration."
  exit 0
fi

echo "Generating Kubernetes custom resource for KMIP configuration ..."
pushd ${PWD}/${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME} > /dev/null 2>&1
#
# The "base64" command takes different parameters for Linux and Mac. For Linux,
# we need to disable line breaks at every 67 characters using the "-w 0" option
#
BASE64CMD=base64
if [[ "$OSTYPE" =~ ^linux* ]]; then
  BASE64CMD="base64 -w 0"
fi
tar cfz hsmconfig-${CLUSTER_NAME}.tgz tokens
HSM_CONFIG=`cat hsmconfig-${CLUSTER_NAME}.tgz | $BASE64CMD`
HSM_SECRETS_FILE=$(cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: hsmconfig-${CLUSTER_NAME}
  namespace: hpe-secure
type: Opaque
data:
  MAPR_KMIP:     "$HSM_CONFIG"
EOF
)

popd > /dev/null 2>&1

OUTPUT_FILE=${PWD}/${HSMSETUP_DIR}/hsm_config/${CLUSTER_NAME}/hsmconfig-${CLUSTER_NAME}.yaml
echo "${HSM_SECRETS_FILE}" > ${OUTPUT_FILE}

echo ""
echo "The KMIP configuration generated for this cluster are available at: $OUTPUT_FILE"
echo "Please copy them to a machine where you can run the following command: "
echo "  kubectl apply -f $OUTPUT_FILE"
