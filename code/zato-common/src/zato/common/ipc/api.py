# -*- coding: utf-8 -*-

"""
Copyright (C) 2023, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import errno
import logging
import os
import stat
import tempfile
from datetime import datetime, timedelta
from io import StringIO
from json import loads
from traceback import format_exc
from uuid import uuid4

try:
    from fcntl import fcntl
except ImportError:
    # Ignore it under Windows
    pass

# gevent
from gevent import sleep

# Zato
from zato.common.api import IPC
from zato.common.ipc.publisher import Publisher
from zato.common.ipc.server import IPCServer
from zato.common.ipc.subscriber import Subscriber
from zato.common.util.api import load_ipc_pid_port
from zato.common.util.file_system import fs_safe_name

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import callable_

# ################################################################################################################################
# ################################################################################################################################

logger = logging.getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

fifo_create_mode = stat.S_IRUSR | stat.S_IWUSR
fifo_ignore_err = errno.EAGAIN, errno.EWOULDBLOCK

# On Linux, this is F_LINUX_SPECIFIC_BASE (1024) + 7
_F_SETPIPE_SZ = 1031

# ################################################################################################################################
# ################################################################################################################################

class IPCAPI:
    """ API through which IPC is performed.
    """
    pid: 'int'
    server: 'IPCServer'
    username: 'str'
    password: 'str'
    on_message_callback: 'callable_'

    def __init__(self) -> 'None':
        self.username = 'ipc'
        self.password = ''

# ################################################################################################################################

    def set_password(self, password:'str') -> 'None':
        self.password = password

# ################################################################################################################################

    def start_server(
        self,
        pid,
        base_dir,     # type: str
        *,
        bind_host='', # type: str
        bind_port='', # type: str
        username='',  # type: str
        password='',  # type: str
    ) -> 'None':

        # stdlib
        import os

        def my_callback(msg:'Bunch') -> 'str':
            return 'Hello'

        server_type_suffix = f':{pid}'

        IPCServer.start(
            base_dir=base_dir,
            bind_host=bind_host,
            bind_port=bind_port,
            username=username,
            password=password,
            callback_func=my_callback,
            server_type_suffix=server_type_suffix
        )

# ################################################################################################################################

    def _get_pid_publisher(self, cluster_name:'str', server_name:'str', target_pid:'int') -> 'Publisher':

        # We do no have a publisher connected to that PID, so we need to create it ..
        if target_pid not in self.pid_publishers:

            # Create a publisher and sleep for a moment until it connects to the other socket
            publisher = Publisher(self.get_endpoint_name(cluster_name, server_name, target_pid), self.pid)

            # We can tolerate it because it happens only the very first time our PID invokes target_pid
            sleep(0.1)

            # We can now store it for later use
            self.pid_publishers[target_pid] = publisher

        # At this point we are sure we have a publisher for target PID
        return self.pid_publishers[target_pid]

# ################################################################################################################################

    def _get_response(self, fifo, buffer_size, read_size=21, fifo_ignore_err=fifo_ignore_err, empty=('', b'', None)):

        try:
            buff = StringIO()
            data = object() # Use a sentinel because '' or None are expected from os.read

            # The most common use-case for IPC are publish/subscribe messages and the most
            # common response is this: 'zs;{"r": {"r": null}}'
            # which is 21 bytes.

            while data not in empty:
                data = os.read(fifo, read_size)
                buff.write(data.decode('utf8') if isinstance(data, bytes) else data)

            response = buff.getvalue()

            status = response[:IPC.STATUS.LENGTH]
            response = response[IPC.STATUS.LENGTH+1:] # Add 1 to account for the separator
            is_success = status == IPC.STATUS.SUCCESS

            if is_success:
                response = loads(response) if response else ''

            buff.close()

            return is_success, response

        except OSError as e:
            if e.errno not in fifo_ignore_err:
                raise

# ################################################################################################################################

    def invoke_by_pid(
        self,
        service,      # type: str
        request,      # type: str
        cluster_name, # type: str
        server_name,  # type: str
        target_pid,   # type: int
        timeout=90    # type: int
    ) -> 'any_':
        """ Invokes a service in a specific process synchronously through IPC.
        """
        ipc_port = load_ipc_pid_port(cluster_name, server_name, target_pid)
        ipc_port
        ipc_port
        '''
        # Create a FIFO pipe to receive replies to come through
        fifo_path = os.path.join(tempfile.tempdir, 'zato-ipc-fifo-{}'.format(uuid4().hex))
        os.mkfifo(fifo_path, fifo_create_mode)

        logger.info('Invoking %s on %s (%s:%s) (%s) with %s',
            service, cluster_name, server_name, target_pid, fifo_path, payload)

        try:
            publisher = self._get_pid_publisher(cluster_name, server_name, target_pid)
            publisher.publish(payload, service, target_pid, reply_to_fifo=fifo_path)

            # Async = we do not need to wait for any response
            if is_async:
                return

            is_success, response = False, None

            try:

                # Open the pipe for reading ..
                fifo_fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
                fcntl(fifo_fd, _F_SETPIPE_SZ, 1000000)

                # .. and wait for response ..
                now = datetime.utcnow()
                until = now + timedelta(seconds=timeout)

                while now < until:
                    sleep(0.05)
                    is_success, response = self._get_response(fifo_fd, fifo_response_buffer_size)
                    if response:
                        break
                    else:
                        now = datetime.utcnow()

            except Exception:
                logger.warning('Exception in IPC FIFO, e:`%s`', format_exc())

            finally:
                os.close(fifo_fd)

            return is_success, response

        except Exception:
            logger.warning(format_exc())
        finally:
            os.remove(fifo_path)
        '''

# ################################################################################################################################
# ################################################################################################################################
