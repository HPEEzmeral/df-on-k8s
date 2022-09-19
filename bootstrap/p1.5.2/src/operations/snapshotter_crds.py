import os

from common.mapr_exceptions.ex import NotFoundException
from operations.operationsbase import OperationsBase
from operations.yamlfile import YamlFile


class SnapshotterCRDs(OperationsBase):
    def __init__(self):
        super(SnapshotterCRDs, self).__init__()
        self.snapshotter_crd_dir = os.path.abspath(os.path.join(self.prereq_dir, "snapshotter-crds"))
        if not os.path.exists(self.snapshotter_crd_dir):
            raise NotFoundException(self.snapshotter_crd_dir)
        self.load_yaml_dict()

    def load_yaml_dict(self):
        file_name = self.check_exists(self.snapshotter_crd_dir, "volumesnapshotclasses.yaml")
        volume_snapshot_classes_yaml_file = YamlFile("volumesnapshotclasses", "volume snapshot classes", file_name, "snapshotter_crds")
        self.yamls.append(volume_snapshot_classes_yaml_file)

        file_name = self.check_exists(self.snapshotter_crd_dir, "volumesnapshotcontents.yaml")
        volume_snapshot_contents_yaml_file = YamlFile("volumesnapshotcontents", "volume snapshot contents", file_name,
                                                     "snapshotter_crds")
        self.yamls.append(volume_snapshot_contents_yaml_file)

        file_name = self.check_exists(self.snapshotter_crd_dir, "volumesnapshots.yaml")
        volume_snapshots_yaml_file = YamlFile("volumesnapshots", "volume snapshots", file_name,
                                                      "snapshotter_crds")
        self.yamls.append(volume_snapshots_yaml_file)

        return True

    def install_snapshottercrd_components(self, upgrade_mode=False):
        installable_yaml_types = ["snapshotter_crds"]
        self.install_components(installable_yaml_types=installable_yaml_types, upgrade_mode=upgrade_mode)

    def uninstall_snapshottercrd_components(self):
        uninstallable_yaml_types = ["snapshotter_crds"]
        self.uninstall_components(uninstallable_yaml_types=uninstallable_yaml_types)
