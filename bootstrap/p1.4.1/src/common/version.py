# __eq__ still defined as an alias in Python 3 to 'eq'
from operator import __eq__
import re

from common.mapr_exceptions.ex import ConversionException

REG_EX_VALID = '^[0-9,\.]*$'
REG_EX = '(\d+)\.?(\d+)?\.?(\d+)?\.?(\d+)?\.?(\d+)?'


class Version(object):
    @staticmethod
    def parse_array(version_array):
        this_version = Version()

        length = len(version_array)

        if length >= 1:
            this_version.major = version_array[0]
        if length >= 2:
            this_version.minor = version_array[1]
        if length >= 3:
            this_version.maint = version_array[2]
        if length >= 4:
            this_version.release = version_array[3]
        if length >= 5:
            this_version.build = version_array[4]

        this_version.valid = True

        return this_version

    @staticmethod
    def parse(version_string):
        this_version = Version()

        re_compile = re.compile(REG_EX_VALID)
        match = re_compile.match(version_string)

        if match is None:
            return this_version

        re_compile = re.compile(REG_EX)
        match = re_compile.match(version_string)

        if match is None or match.group(1) is None:
            return this_version

        this_version.original_string = version_string
        this_version.valid = True
        this_version.major = int(match.group(1))

        if match.group(2) is not None:
            this_version.minor = int(match.group(2))
            if match.group(3) is not None:
                this_version.maint = int(match.group(3))
                if match.group(4) is not None:
                    this_version.release = int(match.group(4))
                    if match.group(5) is not None:
                        this_version.build = int(match.group(5))

        return this_version

    @staticmethod
    def _correct_object_type(variable):
        if variable is None:
            return None

        if isinstance(variable, int):
            return variable

        if isinstance(variable, str):
            return int(variable)

        raise ConversionException('%s is an invalid type to convert to a version integer' % type(variable))

    def __init__(self, major=None, minor=None, maint=None, release=None, build=None):
        self.original_string = None
        self.major = Version._correct_object_type(major)
        self.minor = Version._correct_object_type(minor)
        self.maint = Version._correct_object_type(maint)
        self.release = Version._correct_object_type(release)
        self.build = Version._correct_object_type(build)

        if major is not None or minor is not None or maint is not None or release is not None or build is not None:
            self.valid = True
        else:
            self.valid = False

    def __str__(self):
        if self.valid is False:
            return 'No version'

        s = str(self.major)
        if self.minor is not None:
            s += '.' + str(self.minor)
            if self.maint is not None:
                s += '.' + str(self.maint)
                if self.release is not None:
                    s += '.' + str(self.release)
                    if self.build is not None:
                        s += '.' + str(self.build)

        return s

    def __eq__(self, other):
        if self.major == other.major and self.minor == other.minor and \
                self.maint == other.maint and self.release == other.release and self.build == other.build:
            return True

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if __eq__(self, other):
            return False

        return self.__test_lt__(other)

    def __le__(self, other):
        if __eq__(self, other):
            return True

        return self.__test_lt__(other)

    def __gt__(self, other):
        if __eq__(self, other):
            return False

        return self.__test_gt__(other)

    def __ge__(self, other):
        if __eq__(self, other):
            return True

        return self.__test_gt__(other)

    def __test_gt__(self, other):
        if self.major is not None and other.major is not None:
            if self.major > other.major:
                return True
            if self.major < other.major:
                return False
        if self.minor is not None and other.minor is not None:
            if self.minor > other.minor:
                return True
            if self.minor < other.minor:
                return False
        if self.maint is not None and other.maint is not None:
            if self.maint > other.maint:
                return True
            if self.maint < other.maint:
                return False
        if self.release is not None and other.release is not None:
            if self.release > other.release:
                return True
            if self.release < other.release:
                return False
        if self.build is not None and other.build is not None:
            if self.build > other.build:
                return True
            if self.build < other.build:
                return False

        return False

    def __test_lt__(self, other):
        if self.major is not None and other.major is not None:
            if self.major < other.major:
                return True
            if self.major > other.major:
                return False
        if self.minor is not None and other.minor is not None:
            if self.minor < other.minor:
                return True
            if self.minor > other.minor:
                return False
        if self.maint is not None and other.maint is not None:
            if self.maint < other.maint:
                return True
            if self.maint > other.maint:
                return False
        if self.release is not None and other.release is not None:
            if self.release < other.release:
                return True
            if self.release > other.release:
                return False
        if self.build is not None and other.build is not None:
            if self.build < other.build:
                return True
            if self.build > other.build:
                return False

        return False
