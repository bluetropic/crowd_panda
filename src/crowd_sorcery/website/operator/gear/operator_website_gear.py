# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.gear import *

operator_route = route_for('operator')


@operator_route('GET', '/gears')
def list_gears_widget():
    return get_template('list-gear.html').render(not_activated_gears=list_not_activated_gears())


@operator_route('POST', '/gears/{{ gear_id }}/activation', gear_id='\d+')
def activate_gear_action():
    activate_gear(**get_http_arguments())