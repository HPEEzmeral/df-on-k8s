
class MapRException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NotFoundException(MapRException):
    def __init__(self, value):
        MapRException.__init__(self, value)


class NotImplementedException(MapRException):
    def __init__(self, value):
        MapRException.__init__(self, value)


class ConversionException(MapRException):
    def __init__(self, value):
        MapRException.__init__(self, value)


class InstallException(MapRException):
    def __init__(self, value):
        MapRException.__init__(self, value)


class InstallPromptException(InstallException):
    def __init__(self, value):
        InstallException.__init__(self, value)


class InstallDirectoryExistsException(InstallException):
    def __init__(self, value):
        InstallException.__init__(self, value)


class AzureException(InstallException):
    def __init__(self, value):
        InstallException.__init__(self, value)
