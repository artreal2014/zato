# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import re
import string
from datetime import datetime

# ################################################################################################################################

if 0:
    from zato.common.typing_ import callable_

# ################################################################################################################################

_re_fs_safe_name = '[{}]'.format(string.punctuation + string.whitespace)

# ################################################################################################################################

def fs_safe_name(value:'str') -> 'str':
    return re.sub(_re_fs_safe_name, '_', value)

# ################################################################################################################################

def fs_safe_now(_utcnow:'callable_'=datetime.utcnow) -> 'str':
    """ Returns a UTC timestamp with any characters unsafe for filesystem names removed.
    """
    return fs_safe_name(_utcnow().isoformat())

# ################################################################################################################################
