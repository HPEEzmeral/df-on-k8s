from common.mapr_logger.log import Log
from mapr.clouds.cloud import Cloud


class AWSCloud(Cloud):
    NAME = "AWS"

    def __init__(self):
        super(AWSCloud, self).__init__()

    def get_name(self):
        return AWSCloud.NAME

    def is_enabled(self):
        self.enabled = False
        return self.enabled

    def is_available(self):
        if not self.enabled:
            return False

        self.available = False
        return self.available

    def build_cloud(self):
        Log.info("{0} build_cloud() is not implemented yet".format(AWSCloud.NAME))

    def configure_cloud(self):
        Log.info("{0} configure_cloud() is not implemented yet".format(AWSCloud.NAME))
