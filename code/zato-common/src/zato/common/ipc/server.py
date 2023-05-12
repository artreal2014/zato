# -*- coding: utf-8 -*-

"""
Copyright (C) 2023, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from logging import getLogger

# Zato
from zato.common.aux_server.base import AuxServer, AuxServerConfig
from zato.common.crypto.api import ServerCryptoManager

# ################################################################################################################################
# ################################################################################################################################

logger = getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

class IPCServerConfig(AuxServerConfig):
    ipc_port: 'int'

# ################################################################################################################################
# ################################################################################################################################

class IPCServer(AuxServer):
    needs_logging_setup = False
    cid_prefix = 'zipc'
    server_type = 'IPCServer'
    conf_file_name = 'server.conf'
    config_class = AuxServerConfig
    crypto_manager_class = ServerCryptoManager

# ################################################################################################################################
# ################################################################################################################################

def main():

    # stdlib
    import os

    bind_port = 27050
    root_dir = os.environ['Zato_Test_Server_Root_Dir']
    IPCServer.start(root_dir=root_dir, bind_port=bind_port)

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':
    main()

# ################################################################################################################################
# ################################################################################################################################
