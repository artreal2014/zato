# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from datetime import datetime
from typing import Optional as optional

# Zato
from zato.common.api import GENERIC
from zato.common.ext.dataclasses import dataclass
from zato.common.json_internal import dumps
from zato.common.odb.model import SSOSession as SessionModel
from zato.sso import const

# ################################################################################################################################
# ################################################################################################################################

SessionModelTable = SessionModel.__table__
SessionModelInsert = SessionModelTable.insert

# ################################################################################################################################
# ################################################################################################################################

@dataclass(init=False)
class SessionInsertCtx:
    ust: str
    creation_time: datetime
    expiration_time: datetime
    user_id: int
    auth_type: str
    auth_principal: str
    remote_addr: str
    user_agent: str
    ctx_source: str
    ext_session_id: optional[str]
    interaction_max_len: int

# ################################################################################################################################
# ################################################################################################################################

def insert_sso_session(sql_session, insert_ctx, needs_commit=True):
    # type: (object, SessionInsertCtx, bool) -> None

    # Create current interaction details for this SSO session ..
    session_state_change_list = update_session_state_change_list(
        [],
        insert_ctx.interaction_max_len,
        insert_ctx.remote_addr,
        insert_ctx.user_agent,
        insert_ctx.ctx_source,
        insert_ctx.creation_time,
    )

    # .. convert interaction details into an opaque attribute ..
    opaque = dumps({
        'session_state_change_list': session_state_change_list
    })

    # .. run the SQL insert statement ..
    sql_session.execute(
        SessionModelInsert().values({
            'ust': insert_ctx.ust,
            'creation_time': insert_ctx.creation_time,
            'expiration_time': insert_ctx.expiration_time,
            'user_id': insert_ctx.user_id,
            'auth_type': insert_ctx.auth_type or const.auth_type.default,
            'auth_principal': insert_ctx.auth_principal,
            'remote_addr': ', '.join(str(elem) for elem in insert_ctx.remote_addr),
            'user_agent': insert_ctx.user_agent,
            'ext_session_id': insert_ctx.ext_session_id,
            GENERIC.ATTR_NAME: opaque
    }))

    # .. and commit the SQL state.
    if needs_commit:
        sql_session.commit()

# ################################################################################################################################
# ################################################################################################################################

def update_session_state_change_list(current_state, interaction_max_len, remote_addr, user_agent, ctx_source, now):
    """ Adds information about a user interaction with SSO, keeping the history
    of such interactions to up to max_len entries.
    """
    # type: (list, int, str, str, str, datetime)
    if current_state:
        idx = current_state[-1]['idx']
    else:
        idx = 0

    remote_addr = remote_addr if isinstance(remote_addr, list) else [remote_addr]

    if len(remote_addr) == 1:
        remote_addr = str(remote_addr[0])
    else:
        remote_addr = [str(elem) for elem in remote_addr]

    current_state.append({
        'remote_addr': remote_addr,
        'user_agent': user_agent,
        'timestamp_utc': now.isoformat(),
        'ctx_source': ctx_source,
        'idx': idx + 1
    })

    if len(current_state) > interaction_max_len:
        current_state.pop(0)

    return current_state

# ################################################################################################################################