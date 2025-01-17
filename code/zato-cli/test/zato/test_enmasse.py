# -*- coding: utf-8 -*-

"""
Copyright (C) 2023, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os
from logging import basicConfig, getLogger, WARN
from tempfile import gettempdir
from traceback import format_exc
from unittest import main, TestCase

# Bunch
from bunch import Bunch

# Zato
from zato.common.test.config import TestConfig
from zato.common.test import rand_string, rand_unicode
from zato.common.util.open_ import open_w

# ################################################################################################################################
# ################################################################################################################################

basicConfig(level=WARN, format='%(asctime)s - %(message)s')
logger = getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from sh import RunningCommand
    from zato.common.typing_ import any_

# ################################################################################################################################
# ################################################################################################################################

template = """

channel_plain_http:
  - connection: channel
    is_active: true
    is_internal: false
    merge_url_params_req: true
    name: /test/enmasse1/{test_suffix}
    params_pri: channel -params-over-msg
    sec_def: zato-no-security
    service: pub.zato.ping
    service_name: pub.zato.ping
    transport: plain_http
    url_path: /test/enmasse1/{test_suffix}
  - connection: channel
    is_active: true
    is_internal: false
    merge_url_params_req: true
    name: /test/enmasse2/{test_suffix}
    params_pri: channel-params-over-msg
    sec_def: zato-no-security
    service: pub.zato.ping
    service_name: pub.zato.ping
    transport: plain_http
    url_path: /test/enmasse2/{test_suffix}

zato_generic_connection:
    - address: ws://localhost:12345
      cache_expiry: 0
      has_auto_reconnect: true
      is_active: true
      is_channel: true
      is_internal: false
      is_outconn: false
      is_zato: true
      name: test.enmasse.{test_suffix}
      on_connect_service_name: pub.zato.ping
      on_message_service_name: pub.zato.ping
      pool_size: 1
      sec_use_rbac: false
      security_def: ZATO_NONE
      subscription_list:
      type_: outconn-wsx
      # These are taken from generic.connection.py -> extra_secret_keys
      oauth2_access_token: null
      consumer_key: null
      consumer_secret: null

def_sec:
  - name: "Test Basic Auth {test_suffix}"
    is_active: true
    type: basic_auth
    username: "MyUser {test_suffix}"
    password: "MyPassword"
    realm: "My Realm"

email_smtp:
  - name: {smtp_config.name}
    host: {smtp_config.host}
    is_active: true
    is_debug: false
    mode: starttls
    port: 587
    timeout: 300
    username: {smtp_config.username}
    password: {smtp_config.password}
    ping_address: {smtp_config.ping_address}

"""

# ################################################################################################################################
# ################################################################################################################################

class EnmasseTestCase(TestCase):

# ################################################################################################################################

    def get_smtp_config(self) -> 'Bunch':
        out = Bunch()

        out.name         = os.environ.get('Zato_Test_Enmasse_SMTP_Name')
        out.host         = os.environ.get('Zato_Test_Enmasse_SMTP_Host')
        out.username     = os.environ.get('Zato_Test_Enmasse_SMTP_Username')
        out.password     = os.environ.get('Zato_Test_Enmasse_SMTP_Password')
        out.ping_address = os.environ.get('Zato_Test_Enmasse_SMTP_Ping_Address')

        return out

# ################################################################################################################################

    def _warn_on_error(self, stdout:'any_', stderr:'any_') -> 'None':
        logger.warning(format_exc())
        logger.warning('stdout -> %s', stdout)
        logger.warning('stderr -> %s', stderr)

# ################################################################################################################################

    def _assert_command_line_result(self, out:'RunningCommand') -> 'None':

        self.assertEqual(out.exit_code, 0)

        stdout = out.stdout.decode('utf8')
        stderr = out.stderr.decode('utf8')

        if 'error' in stdout:
            self._warn_on_error(stdout, stderr)
            self.fail('Found an error in stdout while invoking enmasse')

        if 'error' in stderr:
            self._warn_on_error(stdout, stderr)
            self.fail('Found an error in stderr while invoking enmasse')

# ################################################################################################################################

    def _invoke_command(self, config_path:'str', require_ok:'bool'=True) -> 'RunningCommand':

        # Zato
        from zato.common.util.cli import get_zato_sh_command

        # A shortcut
        command = get_zato_sh_command()

        # Invoke enmasse ..
        out = command('enmasse', TestConfig.server_location,
            '--import', '--input', config_path, '--replace-odb-objects', '--verbose')

        # .. if told to, make sure there was no error in stdout/stderr ..
        if require_ok:
            self._assert_command_line_result(out)

        return out

# ################################################################################################################################

    def _cleanup(self, test_suffix:'str') -> 'None':

        # Zato
        from zato.common.util.cli import get_zato_sh_command

        # A shortcut
        command = get_zato_sh_command()

        # Build the name of the connection to delete
        conn_name = f'test.enmasse.{test_suffix}'

        # Invoke the delete command ..
        out = command(
            'delete-wsx-outconn',
            '--path', TestConfig.server_location,
            '--name', conn_name
        )

        # .. and make sure there was no error in stdout/stderr ..
        self._assert_command_line_result(out)

# ################################################################################################################################

    def test_enmasse_ok(self) -> 'None':

        # sh
        from sh import ErrorReturnCode

        tmp_dir = gettempdir()
        test_suffix = rand_unicode() + '.' + rand_string()

        file_name = 'zato-enmasse-' + test_suffix + '.yaml'
        config_path = os.path.join(tmp_dir, file_name)

        smtp_config = self.get_smtp_config()

        data = template.format(test_suffix=test_suffix, smtp_config=smtp_config)

        f = open_w(config_path)
        _ = f.write(data)
        f.close()

        try:
            # Invoke enmasse to create objects ..
            _ = self._invoke_command(config_path)

            # .. now invoke it again to edit them in place.
            _ = self._invoke_command(config_path)

        except ErrorReturnCode as e:
            stdout = e.stdout # type: bytes
            stdout = stdout.decode('utf8') # type: ignore
            stderr = e.stderr

            self._warn_on_error(stdout, stderr)
            self.fail(f'Caught an exception while invoking enmasse; stdout -> {stdout}')

        finally:
            self._cleanup(test_suffix)

# ################################################################################################################################

    def test_enmasse_service_does_not_exit(self) -> 'None':

        tmp_dir = gettempdir()
        test_suffix = rand_unicode() + '.' + rand_string()

        file_name = 'zato-enmasse-' + test_suffix + '.yaml'
        config_path = os.path.join(tmp_dir, file_name)

        smtp_config = self.get_smtp_config()

        # Note that we replace pub.zato.ping with a service that certainly does not exist
        data = template.replace('pub.zato.ping', 'zato-enmasse-service-does-not-exit')
        data = data.format(test_suffix=test_suffix, smtp_config=smtp_config)

        f = open_w(config_path)
        _ = f.write(data)
        f.close()

        # Invoke enmasse to create objects (which will fail because the service used above does not exist)
        out = self._invoke_command(config_path, require_ok=False)

        stdout = out.stdout # type: any_
        stdout = stdout.decode('utf8')
        stderr = out.stderr

        if not '3 errors found' in stdout:
            self._warn_on_error(stdout, stderr)
            self.fail('Expected for enmasse to return errors')

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':
    _ = main()


# ################################################################################################################################
