#!/usr/bin/env bash
ECHOE="echo -e"

kubectl get secrets dataplatform-client-secrets -n hpe-externalclusterinfo -o yaml | sed -e 's/apiVersion.*$//' | sed -n -e '/kind: Secret/q;p' > /tmp/client-secrets.yaml
kubectl get secrets dataplatform-server-secrets -n hpe-externalclusterinfo -o yaml | sed -e 's/apiVersion.*$//' | sed -n -e '/kind: Secret/q;p' > /tmp/server-secrets.yaml
kubectl get secrets dataplatform-user-secrets -n hpe-externalclusterinfo -o yaml | sed -e 's/apiVersion.*$//' | sed -n -e '/kind: Secret/q;p' > /tmp/user-secrets.yaml
kubectl get cm dataplatform-external-cm -n hpe-externalclusterinfo -o yaml | sed -e 's/apiVersion.*$//' | sed -n -e '/kind: ConfigMap/q;p' > /tmp/external-cm.yaml
kubectl get cm dataplatform-hivesite-cm -n hpe-externalclusterinfo -o yaml | sed -e 's/apiVersion.*$//' | sed -n -e '/kind: ConfigMap/q;p' > /tmp/hivesite-cm.yaml
kubectl get dataplatform | grep -v NAME | awk '{print $1}' > /tmp/dataplatform.namespace

dataplatform=$(kubectl get dataplatform | grep -v NAME | awk '{print $1}')
kubectl cp gen-external-secrets.sh $dataplatform/admincli-0:/tmp
kubectl cp /tmp/client-secrets.yaml $dataplatform/admincli-0:/tmp
kubectl cp /tmp/server-secrets.yaml $dataplatform/admincli-0:/tmp
kubectl cp /tmp/user-secrets.yaml $dataplatform/admincli-0:/tmp
kubectl cp /tmp/external-cm.yaml $dataplatform/admincli-0:/tmp
kubectl cp /tmp/hivesite-cm.yaml $dataplatform/admincli-0:/tmp
kubectl cp /tmp/dataplatform.namespace $dataplatform/admincli-0:/tmp
kubectl exec -i admincli-0 -n $dataplatform -- /bin/bash -c "cd /tmp; ./gen-external-secrets.sh" | tee /tmp/gen-external-secrets.output
filename=$(grep apply /tmp/gen-external-secrets.output | awk '{print $4}')
kubectl cp $dataplatform/admincli-0:/tmp/$filename $filename
