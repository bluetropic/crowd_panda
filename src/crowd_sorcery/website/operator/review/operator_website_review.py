# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.review import *
from crowd_sorcery.feature.task import *

operator_route = route_for('operator')


@operator_route('GET', '/reviews')
def list_operator_reviews_page():
    return get_template('list-reviews.html').render(waiting_for_operator_reviews=list_waiting_for_operator_reviews())


@operator_route('PUT', '/task-results/{{ id }}/status', id='\d+')
def update_task_result_status_action():
    update_task_result_status_by_op(**get_http_arguments())
