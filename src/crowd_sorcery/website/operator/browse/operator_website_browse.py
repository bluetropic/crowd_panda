# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.profile.web import *
from crowd_sorcery.feature.operator import *

operator_public_route = route_for('operator', tags=(TAG_NO_LOGIN_REQUIRED,))
operator_route = route_for('operator')

LOGGER = logging.getLogger(__name__)


@operator_route('GET', '/')
def operator_home_page():
    return get_template('operator-home.html').render()


@operator_public_route('GET', '/login')
def operator_login_page():
    if get_current_operator_id():
        redirect_to('/')
    return get_template('operator-login.html').render()


@operator_public_route('POST', '/session')
def operator_login_action():
    request = get_current_http_request()
    username = get_http_argument('username', optional=True)
    password = get_http_argument('password', optional=True)
    try:
        operator_login(username, password)
    except InvalidCredential as e:
        LOGGER.warn('[sensitive]login failed: %(site)s, %(function)s, %(username)s, %(reason)s, %(remote_ip)s, %(user_agent)s', {
            'site': 'operator',
            'function': 'login',
            'username': username,
            'reason': e.message,
            'remote_ip': request.remote_ip,
            'user_agent': request.headers.get('User-Agent')
        })
        raise InvalidCommand({'@': e.message})
    else:
        LOGGER.info('[sensitive]login succeeded: %(site)s, %(function)s, %(username)s, %(remote_ip)s, %(user_agent)s', {
            'site': 'operator',
            'function': 'login',
            'username': username,
            'remote_ip': request.remote_ip,
            'user_agent': request.headers.get('User-Agent')
        })


@operator_route('GET', '/logout')
def operator_logout_action():
    remove_current_signed_in_operator()
    redirect_to('/')