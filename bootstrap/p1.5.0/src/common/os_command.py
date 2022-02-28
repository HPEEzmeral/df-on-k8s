import subprocess

from common.mapr_logger.log import Log


class OSCommand(object):
    @staticmethod
    def run(statements):
        response, status = OSCommand.run2(statements)
        return response

    @staticmethod
    def run3(statements, username=None, use_nohup=False, out_file=None, in_background=False, users_env=False, truncate_response=-1):
        responses, status = OSCommand.run2(statements, username, use_nohup, out_file, in_background, users_env, truncate_response)
        return responses, status, statements

    @staticmethod
    def run2(statements, username=None, use_nohup=False, out_file=None, in_background=False, users_env=False, truncate_response=-1):
        if isinstance(statements, str):
            statements = [statements]

        responses = ''
        status = 0

        for statement in statements:
            new_statement = ''
            if use_nohup:
                new_statement += 'nohup '
            if username is not None:
                new_statement += 'sudo '
                if users_env:
                    new_statement += '-E '
                new_statement += '-u ' + username + ' ' + statement
            else:
                new_statement += statement

            if in_background:
                if use_nohup and out_file is not None:
                    new_statement += ' > ' + out_file + ' 2>&1'
                else:
                    new_statement += ' &>/dev/null'
                new_statement += ' &'

            Log.debug('RUN: %s' % new_statement)

            process = subprocess.Popen('%s 2>&1' % new_statement, shell=True, stdout=subprocess.PIPE)
            response = process.stdout.read()
            # process.wait will only return None if the process hasn't terminated. We don't
            # need to check for None here
            status = process.wait()

            if len(response) == 0:
                response = '<no response>'
            else:
                # Python 3 returns byes or bytearray from the read() above
                if not isinstance(response, str) and isinstance(response, (bytes, bytearray)):
                    response = response.decode("UTF-8")
            Log.debug('STATUS: %s' % str(status))
            if truncate_response > -1:
                info = (response[:truncate_response] + '...(TEXT TRUNCATED)...') if len(response) > truncate_response else response
                Log.debug('RESPONSE: %s' % info)
            else:
                Log.debug('RESPONSE: %s' % response)

            responses += response

            if status != 0:
                break

        return responses, status

    @staticmethod
    def run2_nolog(statements):
        if isinstance(statements, str):
            statements = [statements]

        responses = ""
        status = 0

        for statement in statements:
            process = subprocess.Popen("%s 2>&1" % statement, shell=True, stdout=subprocess.PIPE)
            response = process.stdout.read()
            # process.wait will only return None if the process hasn't terminated. We don't
            # need to check for None here
            status = process.wait()

            responses += response

            if status != 0:
                break

        return responses, status
