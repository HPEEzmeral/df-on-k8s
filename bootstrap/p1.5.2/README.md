# MapR on Kubernetes Bootstrap Installer

This script will bootstrap your Kubernetes environment for MapR.

## How to Install

1. Run "./bootstrap.sh install" to bootstrap your environment and answer the various prompts. This will install various files in system namespaces for MapR (mapr-system, mapr-external-info, mapr-configuration, drill-operator, spark-operator) inside Kubernetes.
2. Install any MapR CSpace custom resources to create new CSpaces. For Example: kubectl apply -f 'your CSpace custom resource' This will create pods in a new CSpace namespace specified by the CR.
