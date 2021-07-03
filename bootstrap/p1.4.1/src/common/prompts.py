from __future__ import print_function
try:
    import ConfigParser as cp  # Python 2
except ImportError:
    # noinspection PyUnresolvedReferences
    import configparser as cp  # Python 3
import getpass
import os
import re
import sys

from common.mapr_logger.log import Log
from common.parser import Parser
from common.mapr_exceptions.ex import InstallPromptException, InstallException


class Prompts(object):
    PROMPT_MODE = 0
    RECORD_MODE = 1
    HEADLESS_MODE = 2
    PROMPT_MODE_STR = 'PROMPT_MODE'
    RECORD_MODE_STR = 'RECORD_MODE'
    HEADLESS_MODE_STR = 'HEADLESS_MODE'

    _instance = None
    _os_version = ""
    _key_reg_ex = re.compile('^[A-Z][A-Z0-9_]+[A-Z0-9]$')

    @staticmethod
    def validate_commandline_options(mode, response_file):
        # no mode or prompt mode doesn't need a response file
        if mode is None or mode.upper() == Prompts.PROMPT_MODE_STR:
            return Prompts.PROMPT_MODE, None

        if mode.upper() == Prompts.RECORD_MODE_STR:
            if response_file is None:
                raise InstallPromptException('Cannot use the --mode=RECORD_MODE option without '
                                             'the --response_file option')
            return Prompts.RECORD_MODE, Prompts._fix_path(response_file)

        if mode.upper() == Prompts.HEADLESS_MODE_STR:
            if response_file is None:
                raise InstallPromptException('Cannot use the --mode=HEADLESS_MODE option without '
                                             'the --response_file option')
            return Prompts.HEADLESS_MODE, Prompts._fix_path(response_file)

        # shouldn't get here
        raise InstallPromptException('Unsupported mode %s' % mode)

    @staticmethod
    def _fix_path(path):
        expanduser = os.path.expanduser(path)
        realpath = os.path.realpath(expanduser)

        return realpath

    @staticmethod
    def initialize(mode=PROMPT_MODE, response_file=None):
        if Prompts._instance is not None:
            raise InstallException('Prompts is already initialized.')

        Prompts._instance = Prompts(mode, response_file)
        return Prompts._instance

    @staticmethod
    def get_instance():
        if Prompts._instance is None:
            raise InstallException('Prompts is not initialized.')

        return Prompts._instance

    def __init__(self, mode, response_file):
        if mode != Prompts.PROMPT_MODE and mode != Prompts.RECORD_MODE and mode != Prompts.HEADLESS_MODE:
            raise InstallException('Invalid prompt mode %s' % str(mode))

        self.response_file = None
        self.mode = mode
        self.recorded_options = dict()
        self.headless_parser = None

        if mode == Prompts.HEADLESS_MODE:
            if response_file is None:
                raise InstallException('In order to run in headless mode, you must supply a response file.')
            if not os.path.exists(response_file):
                raise InstallException(
                    'In order to run in headless mode, you must supply an existing response file. %s does not exist.' %
                    response_file)
            self.headless_parser = Parser.get_properties_parser(response_file)
            Log.info('Installer prompts have been initialized in headless mode.')
        elif mode == Prompts.RECORD_MODE:
            if response_file is None:
                raise InstallException('In order to run in record mode, you must supply a response file destination.')
            dirname = os.path.dirname(response_file)
            if not os.path.exists(dirname):
                raise InstallException('In order to run in record mode, the directory for the response file must exist.')
            self.response_file = open(response_file, 'w')
            Log.info('Installer prompts have been initialized in record mode. response file: {0}'.format(response_file))

    def write_response_file(self):
        if Prompts._instance is None:
            Log.debug('Cannot write a response file prompts are not initialized')
            return

        if self.mode != Prompts.RECORD_MODE:
            Log.debug('Cannot write a response file when not in record mode')
            return

        if self.response_file.closed:
            Log.warn('Cannot write a response file that is not opened. Response file can only be written once')
            return

        try:
            sorted_keys = sorted(self.recorded_options)
            for key in sorted_keys:
                self.response_file.write('%s=%s%s' % (key, self.recorded_options[key], os.linesep))
        finally:
            self.response_file.close()

    def prompt(self, prompt, default=None, password=False, newline=False, key_name=None):
        self.check_prompt_key(key_name)

        if self.mode == Prompts.HEADLESS_MODE:
            if key_name is None:
                raise InstallException('key_name cannot be None in headless mode.')

            try:
                value = self.headless_parser.get('root', key_name)
                return value
            except cp.NoOptionError:
                Log.info('%s key_name was not supplied in response file; Ignoring' % key_name)
                return default

        if default is not None:
            prompt += ' [%s]' % default

        while True:
            if not password:
                print('>>> %s:' % prompt, end=' ')
                sys.stdout.flush()

                try:
                    response = raw_input().strip()
                except NameError:
                    response = input().strip()
            else:
                response = Prompts.get_pass('>>> %s: ' % prompt)

            if len(response) == 0:
                response = default

            if password:
                re_prompt = prompt[0:1].lower() + prompt[1:]

                if re_prompt.startswith('enter'):
                    re_prompt = 'Re-%s' % re_prompt
                else:
                    re_prompt = 'Re-enter %s' % re_prompt

                response2 = Prompts.get_pass('>>> %s: ' % re_prompt)
                if len(response2) == 0:
                    response2 = default
                if response2 != response:
                    print('Responses do not match -- try again')
                    continue

            if newline:
                print("")

            if not password:
                Log.info(">>> {0}: {1}".format(prompt, response))
            else:
                Log.info(">>> {0}: <hidden>".format(prompt))

            if self.mode == Prompts.RECORD_MODE:
                if password:
                    self.recorded_options[key_name] = '<enter password here>'
                else:
                    self.recorded_options[key_name] = response

            return response

    def check_prompt_key(self, key_name):
        if key_name is None:
            if self.mode == Prompts.HEADLESS_MODE:
                raise InstallException('A key_name parameter must be supplied when using headless prompt mode.')
            if self.mode == Prompts.RECORD_MODE:
                raise InstallException('A key_name parameter must be supplied when using record prompt mode.')
        else:
            key_name = str(key_name)
            if key_name.upper() != key_name:
                raise InstallException('prompt key_name "%s" string must contain only upper case letters.' % key_name)
            result = Prompts._key_reg_ex.match(key_name)
            if not result:
                raise InstallException(
                    'prompt key_name "%s" string must be alphanumeric, must start with a '
                    'letter, and have underscores which are not at the beginning or end.' % key_name)

    def prompt_boolean(self, prompt_text, default=None, newline=False, key_name=None):
        if default is not None:
            if default:
                default = 'yes'
            else:
                default = 'no'

        prompt_text = '%s (yes/no)' % prompt_text

        while True:
            response = self.prompt(prompt_text, default, newline=newline, key_name=key_name)
            if response is not None:
                if 'YES' == response.upper() or 'Y' == response.upper():
                    return True
                if 'NO' == response.upper() or 'N' == response.upper():
                    return False

            if self.mode == Prompts.HEADLESS_MODE:
                raise InstallException('Invalid boolean value %s for key %s' % (response, key_name))

            print('Select yes or no')

    def prompt_integer(self, prompt_text, default=None, min_val=None, max_val=None, newline=False, key_name=None):
        if min_val is None and max_val is not None:
            raise InstallException('min_val must be set when max_val is set')
        if min_val is not None and max_val is None:
            prompt_text = '%s (>=%d)' % (prompt_text, min_val)
            max_val = sys.maxsize
        elif min_val is not None and max_val is not None:
            prompt_text = '%s (%d-%d)' % (prompt_text, min_val, max_val)

        while True:
            response = self.prompt(prompt_text, default, newline=newline, key_name=key_name)

            # noinspection PyBroadException
            try:
                value = int(response)
                if min_val is not None and value < min_val:
                    if self.mode == Prompts.HEADLESS_MODE:
                        raise InstallException('Invalid integer value %s is less than minimum value %s for key %s.' %
                                               (response, min_val, key_name))

                    print('Value is less than the minimum value %d' % min_val)
                    continue
                if max_val is not None and value > max_val:
                    if self.mode == Prompts.HEADLESS_MODE:
                        raise InstallException('Invalid integer value %s is greater than maximum value %s for key %s.' %
                                               (response, max_val, key_name))

                    print('Value is greater than the maximum value %d' % max_val)
                    continue
                return value
            except Exception:
                if self.mode == Prompts.HEADLESS_MODE:
                    raise InstallException('%s is not a valid integer for key %s.' % (response, key_name))
                print("Illegal value '%s'" % response)

    def prompt_not_none(self, prompt_text, default=None, password=False, newline=False, key_name=None):
        while True:
            result = self.prompt(prompt_text, default, password, newline, key_name)
            if result is not None:
                result = result.strip()
                if len(result) > 0:
                    return result

            Log.warning('Invalid: %s. Please re enter a non empty value.' % prompt_text)

    def prompt_file(self, prompt_text, default=None, newline=False, key_name=None, allow_blank=False):
        while True:
            result = self.prompt(prompt_text, default, newline=newline, key_name=key_name)
            if result is None and not allow_blank:
                if self.mode == Prompts.HEADLESS_MODE:
                    raise InstallException('File path cannot be blank for key %s.' % key_name)

                Log.warning('Path cannot be blank.')
                continue

            if (result is None or result == "None") and allow_blank:
                break

            if not os.path.exists(result):
                if self.mode == Prompts.HEADLESS_MODE:
                    raise InstallException('File path %s does not exist for key %s.' % (result, key_name))

                Log.warning('Path to %s does not exist' % result)
                continue

            break

        return result

    def prompt_choices(self, prompt_text, choices, default=None, newline=False, key_name=None):
        if type(choices) is not list:
            raise InstallException('prompt_choices choice list is not a list.')

        choices_str = str(choices).replace('[', '(').replace(']', ')')
        prompt_text = '%s %s' % (prompt_text, choices_str)
        last_find = None

        if default is not None and default not in choices:
            raise InstallException('The default value %s was not found in the list' % default)

        while True:
            response = self.prompt(prompt_text, default, newline=newline, key_name=key_name)
            find_count = 0

            if response is None:
                if self.mode == Prompts.HEADLESS_MODE:
                    raise InstallException('%s is not a choice in list %s for key %s.' % (response, choices, key_name))

                Log.warning('Enter one of the choices in the list')
                continue

            for item in choices:
                if item.lower().find(response.lower()) >= 0:
                    find_count += 1
                    last_find = item

            if find_count == 0:
                Log.warning('You must enter one of the choices in the list')
            elif find_count >= 2:
                Log.warning('Your entry matched more than one choice')
            else:
                break

        return last_find

    @staticmethod
    def get_pass(prompt):
        passwd = getpass.getpass(prompt)
        return passwd
