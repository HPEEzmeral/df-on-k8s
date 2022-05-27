# 3 node Data Fabric cluster

The goal of 3 node cluster is to provide a lower footprint version of Ezmeral Data Fabric. This can be used to provide customers with lower resources availability a data fabric solution, or to provide sales engineers a lower resource proof of concept for demos. 3 node cluster will be included within Ezmeral Container Platform starting ECP 1.5. 

Included within this directory are three different sample custome resources (CR)s for creating a 3 node cluster on Ezmeral Data Fabric. 
- `3node_full.yaml`
    - This contains a full deployment of 3node. This is similar to a full deployment of a 5 node data fabric cluster, with all components included as part of Ezmeral Data Fabric
- `3node_core_objectstore_gateway.yaml`
    - This CR removes the monitoring stack and only contains the core pods and gateway pods
- `3node_core_objectstore.yaml`
    - This CR is a bare miminum. It contains only the core pods as well as objectstore.

To deploy a 3 node cluster manually, bootstrap Data Fabric, modify one of the CRs above and run `kubectl apply -f 3node.yaml`

# 3 node scheduling and cluster sizing
## Cluster Configuration
There are two main cluster configurations when running a 3 node cluster. 

- 3 Kubernetes Masters AND 3 Kubernetes Workers
    - Total of 6 nodes
    - This is the recommended way to run 3 node data fabric cluster
    - Data fabric pods will be scheduled on the 3 worker nodes by default
        - Set `scheduleonmaster: false` or remove field from CR
- 1 Kubernetes MAster AND 3 Kubernetes Workers
    - Total of 4 nodes
    - Not recommended, but better than just 3 Kubernetes Masters
    - Data fabric pods will be scheduled on the 3 worker nodes by default
        - Set `scheduleonmaster: false` or remove field from CR
- Only 3 Kubernetes Masters
    - Not recommended
    - Total of 3 nodes
    - If there are only 3 nodes total, data fabric MUST need to be scheduled on Kubernetes master nodes as data fabric requires a minimum of 3 nodes. This can be done one of two ways: 
        - Untaint master (not recommended due to variety of reasons, see limitations section for details)
        - Set `scheduleonmaster: true` to allow nodes to tolerate data fabric pods
            - Bootstrap with the option to allow pods to schedule on master

The recommended configuration is a six node cluster, with 3 Kubernetes Master nodes, and 3 Kubernetes Worker Nodes which will be scheduled with data fabric. 

It is not recommended to run a 3 node datafabric cluster on just three nodes. Running a 3 node datafabric cluster on a 3 node Kubernetes cluster has a variety of drawbacks. 
- Kubernetes API server must contend with data fabric for resources
    - There may be instances where resource contention results in non-responsible Kubernetes operations and processes
    - This may seriously impact the stability of the cluster when resources are constrained, especially in smaller sized nodes
    - `kubectl` calls may cease to function
- The Kubernetes cluster itself may be unstable upon node loss
    - If two nodes experience unscheduled shutdowns, the Kubernetes cluster iself may be lost
    - Kubelet service may fail to restart propertly upon node restoration

Kubernetes does not recommend running workloads on Kubernetes Masters due to the issues above, however data fabric has been modified to do so via either taints or tolerations. Please refer to the Kubernetes documentation to understand taints and tolerations here: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

## Node Sizing

The following sizing refer to the nodes which data fabric will run on. They do not refer to the nodes that are for the sole purpose of maintaining the Kubernetes cluster. 


The minimum node sizing for POCs is (per data fabric node):
- 16 cores
- 32GB of memory
- The minimal node sizing for POCs is not recommended for the purposes of production, nor will be supported. This is the bare minimum that data fabric will schedule on.


The minimum supported sizing is (per data fabric node):
- 32 cores
- 64GB of memory
- This is the minimum supported deployment sizing for 3 node data fabric. 

| Configuration | Node Type | Total POC Min CPU | Total POC Min RAM  | Total Supported Min CPU | Total Supported Min RAM |
| ----- | ----- | ----- | ------ | ----- | -----| 
| 3 Master + 3 Worker | Master | 12 cores (4 cores/node) | 48 GB (16 GB/node)  | 12 cores (4 cores/node) | 48 GB (16 GB/node) |
|  | Worker | 48 cores (16 cores/node) | 96 GB (32 GB/node) | 96 cores (32 cores/node) | 192 GB (64 GB/node) | 
| 1 Master + 3 Worker | Master | 4 cores (4 cores/node) |  16 GB (16 GB/node) | 4 cores (4 cores/node)  | 16 GB (16 GB/node) |
|  | Worker | 48 cores (16 cores/node) | 96 GB (32 GB/node) | 96 cores (32 cores/node) | 192 GB (64 GB/node) | 
| 3 Master | Master/Worker | 48 cores (16 cores/node) | 96 GB (32 GB/node) | 96 cores (32 cores/node) | 192 GB (64 GB/node) | 


# 3 node sample CR components


|       | Description | 3node full | Core + Objectstore + Gateway | Core + Objectstore | Role | 
| ----------- | ----------- | -------- | --------- | ---------| ----- | 
| Core      | init       | enabled | enabled | enabled | Creates keys and initializes cluster creation |
|    | admincli | enabled | enabled | enabled | Pod for performing administrative tasks
|    | cldb        | enabled | enabled | enabled | Tracks information about containers
|    | zookeeper        | enabled | enabled | enabled | Coordination service for nodes
|    | mcs       | enabled | enabled | enabled | MapR Control System Webserver
| Gateways | objectstore        | enabled | enabled | enabled | Provides S3 compatible interface
|    | httpfs        | enabled | enabled | disabled | Provides service to enable HTTP REST calls
|    | mapr gateway        | enabled | enabled | disabled | Provides cross cluster communication
|    | data access        | enabled | enabled | disabled | Provides service for JSON REST and OJAI
|    | kafka rest        | enabled | enabled | disabled | Provides service for streams
| Core Services | hivemetastore      | enabled | disabled | disabled | Manages metadata 
| Monitoring | collectd        | enabled | disabled | disabled | Collects system metrics and data
|    | opentsdb        | enabled | disabled | disabled | Provides time series database to store user-specified data
|    | grafana        | enabled | disabled | disabled | UI with graphs of system metrics and data
|    | fluent        | enabled | disabled | disabled | Provides logging endpoints
|    | elasticsearch        | enabled | disabled | disabled | Logging search and analytics engine
|    | kibana        | enabled | disabled | disabled | Navigate Elastic Stack

# 3 node sample resource utilization


|       | Description | 3node full | Core + Objectstore + Gateway | Core + Objectstore |
| ----------- | ----------- | -------- | --------- | ---------| 
|  Pods |  Total  | 20 | 13 | 9|
|CPU (mCPU) | Requested | 40200 | 35000 | 29500 |
|   | Limit | 116000 | 96000 | 77000|
|Memory (GB) | Requested | 142 | 100 | 56 |
|   | Limit | 262 | 220 | 86|
|Disk (GB) | Requested | 445 | 296 | 210 |
|   | Limit | 760 | 512 | 360 |

In the above chart, mCPU, milliCPU, or millicores refers to the unit of measurement of CPU for KUBE. To learn more about mCPU, please refer to the official Kubernetes documentation here: 
https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/


# 3 node in Ezmeral Container Platform

Ezmeral Container Platform will use the Core + Objectstore + Gateway CR in version 5.4
- There will be no dedicated MFS pods
- Please note that MFS will always run as a process within the CLDB pod
- Ezmeral Container Platform will use the Core + Objectstore + Gateway template to deploy its data fabric cluster. This includes:
    - init
    - admincli
    - cldb
    - zookeeper
    - objectstore
    - mcs
    - httpfs
    - mapr gateway
    - data access gateway
    - kafkarest

# 3 node limitations

Due to the smaller footprint and removal of several components usually present on the full deployment, the three node datafabric cluster deployed on Ezmeral Container Platform contains some limitations. 
- One node failover safety threshold
    - Up to one node can safely fail with no major concern
    - While two nodes can fail, there may be manual steps required in recovery
- Removal of monitoring capabilities
    - No grafana or openTSDB
    - MCS relies on data from openTSDB for some of its graphs, however CSI relies on MCS. Thus, MCS graphs and other visual information may be absent from the MCS deployment on 3 node clusters. 
    - Metrics and Monitoring pods may be added to the cluster provided there are enough resources
- No Hive Metastore

# 3 node failover and troubleshooting scenarios

Generally, 3 node datafabric cluster tolerates losing one node fairly well. These are some failure scenarios, how to recover, and the expected behavior.

A 3 node Data Fabric cluster on Ezmeral Container Platform safely supports up to one node failure, similar to the MapR Edge Cluster. Documentation on the MapR Edge Cluster can be found at: https://docs.datafabric.hpe.com/62/MapROverview/MapR-Edge.html. 
## Is my cluster ready?

The easiest way to check if a cluster is ready is via the edf tool in the admincli pod. In the admincli pod, run `edf report ready`. This should report the status of a cluster. Alternatively, `edf report all` will generate a report with more information as to the status of the cluster. 

In the case of a failover scenario, run `edf report ready` after node or pod bringup to determine if recovery was successful. 

## Hardware recovery situations

| Situation | Kubernetes Recovery | Datafabric Recovery | 
| ---------- | ----------| ----------| 
| Unscheduled shutdown of one node | After reboot, ensure all nodes are ready via `kubectl get nodes` and all pods are listed as ready. If Kubernetes nodes are not all ready, follow troubleshooting tips at https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/. | Datafabric nodes should recover by themselves. The CLDBs should reach quorum shortly after nodes come back up and pods are recreated. If they do not, you may wait 30 minutes for the liveness probe to restart the CLDB pod. If they still do not restart, run `edf update`
| Unscheduled shutdown of two nodes | After reboot, ensure all nodes are ready via `kubectl get nodes`. On a minimal 3 node cluster, there may be situations where the Kubernetes cluster is lost. In this case, ensure kubelet is running via `systemctl status kubelet`. If not running, start kubelet via `systemctl start kubelet.service`. If the Kubernetes cluster does not recover, follow steps in https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/ | The CLDBs should reach quorum shortly after nodes come back up and pods are recreated. If they do not, you may wait 30 minutes for the liveness probe to restart the CLDB pod. If they still do not restart, run `edf update`

## Software recovery scenarios

| Situation | Datafabric Recovery | 
| --------- | -------- | 
| 2 CLDB Slave Pods unscheduled shutdown | If CLDB states do not reach quorum after CLDB pods have finished startup, run edf update. | 
| 2 ZK Pods unscheduled shutdown | If CLDB states do not reach quorum after Zookeeper pods have finished startup, run edf update | 
| Edf Startup does not start up pods | If CLDB logs state “Couldn’t connect to CLDB service”, run edf update. Alternatively, you can restart the pods manually. |


# Dev Notes
The CR template in ECP can be found in `mgmt/controller/server/config/base/picasso_core_obj_gway_cr.cfg`

ECP data fabric sizing can be found in `mgmt/controller/server/apps/bd_mgmt/src/k8s/bd_mgmt_datafabric.erl`

ECP created data fabric clusters will automatically determine sizing based on the minimum sizes in these varibles. 
- `MFS_CLDB_MIN_REQ_GB = 16`
- `MFS_CLDB_MIN_MEM_LIMIT_GB = 26`
- `MFS_CLDB_MAX_MEM_GB = 99`

