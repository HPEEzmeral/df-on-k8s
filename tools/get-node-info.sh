#!/usr/bin/env bash
# return codes
NO=0
YES=1
INFO=0
WARN=-1
ERROR=1
NAME_KEY="name"
# labels
USE_NODE_KEY="hpe.com/usenode"
EXCLUDE_NODE="hpe.com/excludenode"
COMPUTE_KEY="hpe.com/compute"
STORAGE_KEY="hpe.com/storage"
NODE_STATUS_KEY="hpe.com/status"
# annotations
TOPOLOGY_KEY="hpe.com/nodetopology"
RACK_KEY="hpe.com/rack"
FULLDISKLIST_KEY="hpe.com/fulldisklist"
SSDLIST_KEY="hpe.com/ssdlist"
HDDLIST_KEY="hpe.com/hddlist"
NVMELIST_KEY="hpe.com/nvmelist"
BOOTSTRAP_VERSION_KEY="hpe.com/bootstrapversion"
NODE_ID_KEY="hpe.com/physicalnodeid"
VALIDATION_STATUS_KEY="hpe.com/validationstatus"

# misc
SEP=","
TRUE="true"
FALSE="false"


declare -A NODE_INFO
declare -A TAINTS
declare -A TAINT_EFFECTS

usage()
{
    echo "usage: get-node-info.sh [[[-f file location ] | [-h]]"
    echo "get-node-info.sh is used to generate a node.info file."
    echo "node.info contains label, annotation, and taint info from your Kubernetes nodes."
    echo "node.info is used by modify-nodes.sh to edit node information."
}

script_tests() {
  error=$NO
  array[0]='test' || error=$YES
  if [ ! $error -eq 0 ]; then
    echo 'ERROR: arrays not supported in this version of bash.'
    exit 1
  fi
  command -v jq > /dev/null
  if [ ! $? -eq 0 ]; then
    echo "ERROR: jq is not installed. Please install jq via 'brew install jq' or 'yum install jq'"
    exit 1
  fi
  command -v kubectl > /dev/null
  if [ ! $? -eq 0 ]; then
    echo "ERROR: kubectl is not installed. Please install kubectl."
    exit 1
  fi

}

create_node_taints() {
  local nodename=$1
  local nodetaints=$(kubectl get node $nodename --no-headers -o=jsonpath='{.items[0].spec.taints}' | cut -c 2- | rev | cut -c 2- | rev | sed 's/ k/|k/g' | sed 's/ e/|e/g' | sed 's/ /\'$'\n/g' | sed 's/|k/ k/g' | sed 's/|e/ e/g' | cut -c 5- | rev | cut -c 2- | rev)
  #echo "NODETAINTS=$nodetaints"
  #nodeinfo["nodetaints"]=$nodetaints
  #NODE_INFO[$nodename]=$nodeinfo
  #local taint_keys=()
  #taint_keys+=( mapr.com/controlplane-mycluster )
  #taint_keys+=( mapr.com/storage-mycluster )
  #local taint_effects=()
  #taint_effects+=( "NoSchedule" )
  #taint_effects+=( "PreferNoSchedule" )
  #local taintcount=0
  #while [ "x${taint_keys[$taintcount]}" != "x" ]
  #do
  #  local nodearray=()
  #  local taint_key=${taint_keys[$taintcount]}
  #  local taint_effect=${taint_effects[$taintcount]}
  #  nodearray=( "$nodename " )
  #  TAINTS[$taint_key]+=$nodearray
  #  TAINT_EFFECTS[$taint_key]=$taint_effect
  #  taintcount=$(( $taintcount + 1 ))
  #done
}

get_all_nodes() {
  NODELIST=(`kubectl get nodes -o jsonpath='{.items[*].metadata.name}'`)
  #get_node_info
  #echo $NODELIST
}

get_all_taints() {
  TAINTLIST=()
  local nodecount=0
  while [ "x${NODELIST[$nodecount]}" != "x" ]
  do
    nodename=${NODELIST[$nodecount]}
    create_node_taints $nodename
    nodecount=$(( $nodecount + 1 ))
  done
  TAINT_KEYS=${!TAINTS[@]}
}

get_excluded_nodes() {
  EXCLUDED_NODELIST=(`kubectl get nodes --selector='!mapr.com/usenode' -o jsonpath='{.items[*].metadata.name}'`)
  #echo $EXCLUDED_NODELIST
}

parse_key() {
  local key=$1
  local type=$2
  local text=$ANNOTATIONS
  if [ $type == "labels" ]; then
    text=$LABELS
  fi
  #line=`echo $2 | grep $1 | cut -f 1 -d ':'`
  local line=$(echo $text | sed 's/ /\'$'\n/g' | grep $key | rev | cut -f 1 -d ':' | rev)
  #line=$(echo $text | grep $key)
  PARSED_VALUE=$line
}

parse_labels_key() {
  local key=$1
  parse_key $1 "labels"
}

parse_annotations_key() {
  local key=$1
  parse_key $1 "annotations"
}

get_bootstrap_version() {
  local text=$1
  parse_annotations_key $BOOTSTRAP_VERSION_KEY
  #BOOTSTRAP_VERSION="unknown"
  BOOTSTRAP_VERSION=$PARSED_VALUE
}

get_compute() {
  local text=$1
  parse_labels_key $COMPUTE_KEY
  #COMPUTE="true"
  COMPUTE=$PARSED_VALUE
}

get_full_disk_list() {
  local text=$1
  parse_annotations_key $FULLDISKLIST_KEY
  #DISK_LIST="/dev/sdb,/dev/sdc,/dev/sdd"
  FULL_DISK_LIST=$PARSED_VALUE
}

get_hdd_list() {
  local text=$1
  parse_annotations_key $HDDLIST_KEY
  #HDD_LIST=""
  HDD_LIST=$PARSED_VALUE
}

get_node_id() {
  local text=$1
  parse_annotations_key $NODE_ID_KEY
  #NODE_ID="2ec32f2fc17fc4d9"
  NODE_ID=$PARSED_VALUE
}

get_node_status() {
  local text=$1
  parse_labels_key $NODE_STATUS_KEY
  #NODE_STATUS="available"
  NODE_STATUS=$PARSED_VALUE
}

get_nvme_list() {
  local text=$1
  parse_annotations_key $NVMELIST_KEY
  #NVME_LIST=""
  NVME_LIST=$PARSED_VALUE
}

get_rack() {
  local text=$1
  parse_annotations_key $RACK_KEY
  #RACK="rack1"
  RACK=$PARSED_VALUE
}

get_ssd_list() {
  local text=$1
  parse_annotations_key $SSDLIST_KEY
  #SSD_LIST="/dev/sdb,/dev/sdc,/dev/sdd"
  SSD_LIST=$PARSED_VALUE
}

get_storage() {
  parse_labels_key $STORAGE_KEY
  #STORAGE="true"
  STORAGE=$PARSED_VALUE
}

get_topology() {
  local text=$1
  parse_annotations_key $TOPOLOGY_KEY
  #TOPOLOGY="/rack1/gke-sky-cluster-default-pool-d71dbf1b-ncsl"
  TOPOLOGY=$PARSED_VALUE
}

get_validation_status() {
  local text=$1
  parse_key $VALIDATION_STATUS_KEY $ANNOTATIONS
  #VALIDATION_STATUS="validated"
  VALIDATION_STATUS=$PARSED_VALUE
}

get_labels() {
  local input=$(kubectl get nodes $nodename --no-headers -o=jsonpath='{.metadata.labels}')
  local firstcut=$(echo $input | cut -c 5-)
  LABELS=$(echo $firstcut | rev | cut -c 2- | rev )
  #LABELS=$(echo $secondcut | sed 's/ /\'$'\n/g')
}

get_annotations() {
  local input=$(kubectl get nodes $nodename --no-headers -o=jsonpath='{.metadata.annotations}')
  local firstcut=$(echo $input | cut -c 5-)
  ANNOTATIONS=$(echo $firstcut | rev | cut -c 2- | rev )
}

create_excluded_node() {
  local nodename=$1
  # add node name
  local value="\"$nodename\""
  echo $value
}

create_node() {
  local nodename=$1
  get_labels
  get_annotations
  local nodestart="{"
  local nodefinish="}"
  echo $nodestart
  # add node name
  local key="\"$NAME_KEY\": "
  local value="\"$nodename\""
  echo $key $value $SEP
  # add compute
  get_compute
  key="\"$COMPUTE_KEY\": "
  value="\"$COMPUTE\""
  echo $key $value $SEP
  # add storage
  get_storage
  key="\"$STORAGE_KEY\": "
  value="\"$STORAGE\""
  echo $key $value $SEP
  # add rack
  get_rack
  key="\"$RACK_KEY\": "
  value="\"$RACK\""
  echo $key $value $SEP
  # add toplogy
  get_topology
  key="\"$TOPOLOGY_KEY\": "
  value="\"$TOPOLOGY\""
  echo $key $value $SEP
  # add fulldisklist
  get_full_disk_list
  key="\"$FULLDISKLIST_KEY\": "
  value="\"$FULL_DISK_LIST\""
  echo $key $value $SEP
  # add ssdlist
  get_ssd_list
  key="\"$SSDLIST_KEY\": "
  value="\"$SSD_LIST\""
  echo $key $value $SEP
  # add hddlist
  get_hdd_list
  key="\"$HDDLIST_KEY\": "
  value="\"$HDD_LIST\""
  echo $key $value $SEP
  # add nvmelist
  get_nvme_list
  key="\"$NVMELIST_KEY\": "
  value="\"$NVME_LIST\""
  echo $key $value $SEP
  # add node id
  get_node_id
  key="\"$NODE_ID_KEY\": "
  value="\"$NODE_ID\""
  # add node status
  get_node_status
  key="\"$NODE_STATUS_KEY\": "
  value="\"$NODE_STATUS\""
  echo $key $value $SEP
  # add bootstrap version
  get_bootstrap_version
  key="\"$BOOTSTRAP_VERSION_KEY\": "
  value="\"$BOOTSTRAP_VERSION\""
  echo $key $value $SEP
  # add validation status
  get_validation_status
  key="\"$VALIDATION_STATUS_KEY\": "
  value="\"$VALIDATION_STATUS\""
  echo $key $value
  echo $nodefinish
}

create_taint() {
  local taintname=$1
  local start="{"
  local finish="}"
  local nodeliststart="\"nodes\": ["
  local nodelistfinish="]"
  local nodearray=( ${TAINTS[$taintname]} )
  local effect=${TAINT_EFFECTS[$taintname]}
  echo "\"$taintname\": $start"
  echo "\"effect\": \"$effect\","
  echo $nodeliststart
  local count=0
  while [ "x${nodearray[$count]}" != "x" ]
  do
    if [ ! $count -eq 0 ]; then
      echo $SEP
    fi
    local node=${nodearray[$count]}
    echo "\""$node"\""
    count=$(( $count + 1 ))
  done
  echo $nodelistfinish $finish
}

create_excluded_nodes() {
  local ex_nodes_start="\"excludednodes\": ["
  local ex_nodes_finish="]"$SEP
  echo $ex_nodes_start
  local count=0
  while [ "x${EXCLUDED_NODELIST[$count]}" != "x" ]
  do
    if [ ! $count -eq 0 ]; then
      echo $SEP
    fi
    local node=${EXCLUDED_NODELIST[$count]}
    create_excluded_node $node
    count=$(( $count + 1 ))
  done
  echo $ex_nodes_finish
}

create_nodes() {
  local nodes_start="\"nodes\": ["
  local nodes_finish="]"$SEP
  echo $nodes_start
  local count=0
  while [ "x${NODELIST[$count]}" != "x" ]
  do
    if [ ! $count -eq 0 ]; then
      echo $SEP
    fi
    local node=${NODELIST[$count]}
    create_node $node
    count=$(( $count + 1 ))
  done
  echo $nodes_finish
}

create_taints() {
  local taints_start="\"taints\": ["
  local taints_finish="]"
  local start="{"
  local finish="}"
  local taint_keys=(${TAINT_KEYS[*]})
  echo $taints_start
  local count=0
  while [ "x${taint_keys[$count]}" != "x" ]
  do
    key=${taint_keys[$count]}
    if [ ! $count -eq 0 ]; then
      echo $SEP
    fi
    echo $start
    create_taint $key
    echo $finish
    count=$(( $count + 1 ))
  done

  echo $taints_finish
}

create_node_lists() {
  local start="{"
  local finish="}"
  echo $start
  create_nodes
  create_excluded_nodes
  create_taints
  echo $finish
}

while [ "$1" != "" ]; do
    case $1 in
        -f | --file )           shift
                                NODE_INFO=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

script_tests
get_all_nodes
get_excluded_nodes
get_all_taints
create_node_lists | jq . > node.info
exit 0
