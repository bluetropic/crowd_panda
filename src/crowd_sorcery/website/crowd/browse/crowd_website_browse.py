# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *

crowd_public_route = route_for('crowd', tags=(TAG_NO_LOGIN_REQUIRED, ))


@crowd_public_route('GET', '/')
def crowd_home_wrap():
    return get_template('home.html').render()
