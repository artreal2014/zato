# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# First thing in the process
from gevent import monkey
monkey.patch_all()

# stdlib
import logging
import os
from logging.config import dictConfig
from traceback import format_exc

# ConcurrentLogHandler - updates stlidb's logging config on import so this needs to stay
import cloghandler
cloghandler = cloghandler # For pyflakes

# YAML
import yaml

# Zato
from zato.common.util import absjoin, get_config, store_pidfile
from zato.scheduler.server import Config, SchedulerServer

def main():

    # Always attempt to store the PID file first
    store_pidfile(os.path.abspath('.'))

    # Capture warnings to log files
    logging.captureWarnings(True)

    config = Config()
    repo_location = os.path.join('.', 'config', 'repo')

    # Logging configuration
    with open(os.path.join(repo_location, 'logging.conf')) as f:
        dictConfig(yaml.load(f))

    # Read config in and make paths absolute
    config.main = get_config(repo_location, 'scheduler.conf')

    if config.main.crypto.use_tls:
        config.main.crypto.ca_certs_location = absjoin(repo_location, config.main.crypto.ca_certs_location)
        config.main.crypto.priv_key_location = absjoin(repo_location, config.main.crypto.priv_key_location)
        config.main.crypto.cert_location = absjoin(repo_location, config.main.crypto.cert_location)

    logger = logging.getLogger(__name__)
    logger.info('Scheduler starting (http{}://{}:{})'.format(
        's' if config.main.crypto.use_tls else '', config.main.bind.host, config.main.bind.port))

    # Fix up configuration so it uses the format internal utilities expect
    for name, job_config in get_config(repo_location, 'startup_jobs.conf', needs_user_config=False).items():
        job_config['name'] = name
        config.startup_jobs.append(job_config)

    # Run the scheduler server
    try:
        SchedulerServer(config).serve_forever()
    except Exception, e:
        logger.warn(format_exc(e))

if __name__ == '__main__':
    main()
