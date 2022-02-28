#!/bin/bash
# remove any pod pin labels put on nodes by previous runs of init pod in previous clusters.
# this script is helpful to reset a cluster that you test with over and over.

removeNodeLabels() {
  ADD_LABEL=$1
  nodeNames=kubectl get nodes -o custom-columns=NAME:.metadata.name | tail -n +2)
  declare -a ssNames
  ssNames=("zk" "cldb" "elasticsearch", "mfs-group1", "mfs-group2", "mfs-group3", \
           "mfs-group4", "objectstore-zone1", "objectstore-zone2", "objectstore-zone3", "objectstore-zone4")

  # we need objectstore also so find statefulsets with the objectstore prefix
  oStatefulSetName=$(${KUBECTL_GET_SS} | tail -n +2 | grep -i "${OBJECTSTORE_PODS_PREFIX}-" | cut -d' ' -f1)
  if [[ -n "$oStatefulSetName" ]]; then
    ssNames+=("${oStatefulSetName}")
  fi

  podsJson=$(${KUBECTL_GET_PODS} -o wide -o json)
  #nodes loop
  for nodeName in ${nodeNames}; do
    nodeModified=0
    nodeJson=$(${KUBECTL_GET_NODES} ${nodeName} -o json)

    #ss loop
    for ssName in "${ssNames[@]}"; do
      if [ ${ADD_LABEL} -eq 0 ]; then
        #remove label, go ahead and remove all, even if not already there
        nodeModified=1
        nodeJson=$(jq 'del(.metadata.labels["hpe.com/'$ssName'-pinned"])' <<< $nodeJson)
      #  nodeJson=$(jq 'del(.metadata.labels | select(.key == "hpe.com/'$ssName'-pinned"))' <<< $nodeJson)
      else
        #add label if needed
        #we want every pod with spec/nodeName matching $nodeName, and that has metadata/generateName = "$ssName-"
        #if the count of that is > 0, we have a found
        #podArray=$(jq -c '.items[]' <<< $podsJson)
        podArray=$(jq -c '.items[]|[.metadata.generateName,.spec.nodeName,.metadata.name]' <<< $podsJson)
        ssFound=0
        for pod in ${podArray}; do
          #format is ["fluent-","kuberlinux4.funkybunch.com"]
          #lose the []
          pod=$(sed -e 's/\[//g' -e 's/\]//g' -e 's/,/ /g' -e 's/\"//g' <<< $pod)
          pod=$(sed -e 's/- / /g' <<< $pod)
          pod=($pod)
          podSSName=(${pod[0]})
          podNodeName=(${pod[1]})
          if [ "$podNodeName" = "$nodeName" ]  && [ "$podSSName" = "$ssName" ]; then
            ssFound=1
            break
          fi
        done
        if [ ${ssFound} -eq 1 ]; then
          #add a label to this node for this ss.  ok to add if already there, not an array
          nodeJson=$(jq '.metadata.labels += {"hpe.com/'$ssName'-pinned": "true"}' <<< $nodeJson)
          nodeModified=1
          echo adding label hpe.com/${ssName}-pinned to node $nodeName for pod ${pod[2]}
        fi
      fi
    done
    if [ ${nodeModified} -eq 1 ]; then
      #update the node
      #echo updating $nodeName
      echo $nodeJson > /tmp/edfmodify.json
      ${KUBECTL_APPLY} /tmp/edfmodify.json 2> /dev/null
    fi
  done
}
