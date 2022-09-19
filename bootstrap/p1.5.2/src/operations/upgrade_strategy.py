from common.mapr_logger.log import Log


class UpgradeStrategy(object):
    def __init__(self, ops):
        super(UpgradeStrategy, self).__init__()
        self.ops = ops

    def upgrade(self, yaml_file):
        raise NotImplementedError


class RemoveAndCreate(UpgradeStrategy):
    def __init__(self, ops):
        super(RemoveAndCreate, self).__init__(ops)

    def upgrade(self, yaml_file):
        if not self.ops.run_kubectl_delete(yaml_file, ignore_not_found=True):
            Log.DEBUG("Failed to remove {0}, cancelling upgrade".format(yaml_file.file_path))
            return False
        return self.ops.run_kubectl_apply(yaml_file)


class Apply(UpgradeStrategy):
    def __init__(self, ops):
        super(Apply, self).__init__(ops)

    def upgrade(self, yaml_file):
        return self.ops.run_kubectl_apply(yaml_file)


class Remove(UpgradeStrategy):
    def __init__(self, ops):
        super(Remove, self).__init__(ops)

    def upgrade(self, yaml_file):
        return self.ops.run_kubectl_delete(yaml_file, ignore_not_found=True)
