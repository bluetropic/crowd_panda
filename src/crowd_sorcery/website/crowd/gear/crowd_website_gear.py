# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.gear import *

crowd_public_route = route_for('crowd', tags=(TAG_NO_LOGIN_REQUIRED,))
crowd_route = route_for('crowd')


@crowd_public_route('GET', '/signup')
def crowd_signup_page():
    if get_current_gear_id():
        redirect_to('/')
    return get_template('crowd-signup.html').render()


@crowd_public_route('POST', '/gears')
def signup_action():
    return create_gear(**get_http_arguments())


@crowd_public_route('GET', '/signin')
def crowd_signin_page():
    if get_current_gear_id():
        redirect_to('/')
    return get_template('crowd-signin.html').render()


@crowd_public_route('POST', '/sessions')
def crowd_signin_action():
    try:
        gear_signin(**get_http_arguments())
    except InvalidCredential as e:
        raise InvalidCommand({'@': 'username or password is not match'})


@crowd_route('GET', '/logout')
def crowd_logout_action():
    remove_current_signed_in_gear()
    redirect_to('/')


@widget
def crowd_user_info_widget():
    return get_template('crowd-user-info.html').render(current_user=get_current_gear())


@crowd_route('GET', '/gears/credits')
def gear_credits_page():
    gear = get_current_gear()
    return get_template('crowd-credit.html').render(gear_credit_logs=list_gear_credit_logs(gear.id), gear=gear)
