import json

from common.mapr_logger.log import Log


class NodeLabels(object):
    MAPR_LABEL = "hpe.com/usenode"
    EXCLUSIVE_LABEL = "hpe.com/exclusivecluster"

    def __init__(self, k8s):
        self.k8s = k8s
        self._node_count = 0
        self._items = None
        self._json = None

    def _get_json(self):
        Log.info("Retrieving node information...", stdout=True)
        result, status = self.k8s.run_get("nodes -o=json")
        if status != 0:
            return None

        self._json = json.loads(result)
        if self._json is None:
            Log.error("No JSON was returned from get nodes command")
            return

        self._items = self._json.get("items")
        if self._items is None:
            Log.error("No items dictionary in get nodes JSON")
            return

        self._node_count = len(self._items)

    def get_mapr_use_node_labels(self, label):
        nodes_set = 0
        nodes_set_true = 0
        nodes_set_false = 0
        nodes_not_set = set()

        for node in self._items:
            node_name = node["metadata"]["name"]
            mapr_usenode = node["metadata"]["labels"].get(label)

            if mapr_usenode is not None:
                mapr_usenode = mapr_usenode.lower()
                nodes_set += 1
                Log.info("Node: {0} has {1} label set to: {2}".format(node_name, label, mapr_usenode))
                if mapr_usenode == 'true':
                    nodes_set_true += 1
                elif mapr_usenode == 'false':
                    nodes_set_false += 1
                else:
                    Log.error("Node: {0} has {1} label set to the invalid value of: {2} ".format(node_name, label, mapr_usenode))
            else:
                nodes_not_set.add(node_name)
                Log.info("Node: {0} does not have {1} label set".format(node_name, label))

        Log.info("{0} node(s) found:".format(self._node_count), stdout=True)
        Log.info("- {0} have a {1} tag set to true and will be included".format(nodes_set_true, label), stdout=True)
        Log.info("- {0} do not have a {1} tag and will be included".format(len(nodes_not_set), label), stdout=True)
        Log.info("- {0} have a {1} tag set to false and will NOT be included".format(nodes_set_false, label), stdout=True)
        return nodes_not_set

    def get_mapr_exclusive_labels(self, label):
        nodes_not_set = set()
        nodes_set_none = 0

        for node in self._items:
            node_name = node["metadata"]["name"]
            mapr_exclusive = node["metadata"]["labels"].get(label)

            if mapr_exclusive is not None:
                mapr_exclusive = mapr_exclusive.lower()
                Log.info("Node: {0} has {1} label set to: {2}".format(node_name, label, mapr_exclusive))
                if mapr_exclusive == 'none':
                    nodes_set_none += 1
            else:
                Log.info("Node: {0} does not have {1} label set".format(node_name, label))
                nodes_not_set.add(node_name)

        Log.info("- {0} have a {1} tag set to None".format(nodes_set_none, label), stdout=True)
        Log.info("- {0} do not have a {1} tag and will be set to 'None'".format(len(nodes_not_set), label), stdout=True)
        Log.info("- {0} have a {1} tag set to a specific value".format(self._node_count-len(nodes_not_set)-nodes_set_none, label), stdout=True)
        return nodes_not_set

    def process_labels(self):
        self._get_json()

        nodes_not_set = self.get_mapr_use_node_labels(NodeLabels.MAPR_LABEL)
        if nodes_not_set is not None and len(nodes_not_set) > 0:
            Log.info("Setting MapR usage tag {0} for {1} nodes...".format(NodeLabels.MAPR_LABEL, len(nodes_not_set)))
            for node_not_set in nodes_not_set:
                self.k8s.run_label_mapr_node(node_not_set, NodeLabels.MAPR_LABEL, True)

        nodes_not_set = self.get_mapr_exclusive_labels(NodeLabels.EXCLUSIVE_LABEL)
        if nodes_not_set is not None and len(nodes_not_set) > 0:
            Log.info("Setting MapR usage tag {0} for {1} nodes...".format(NodeLabels.EXCLUSIVE_LABEL, len(nodes_not_set)))
            for node_not_set in nodes_not_set:
                self.k8s.run_label_mapr_node(node_not_set, NodeLabels.EXCLUSIVE_LABEL, "None")
