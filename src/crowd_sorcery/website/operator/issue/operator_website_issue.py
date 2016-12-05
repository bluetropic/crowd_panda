# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.issue import *

operator_route = route_for('operator')


@operator_route('GET', '/issues')
def list_issue_widget():
    return get_template('list-issue.html').render(issues=list_issues())


@operator_route('GET', '/issues/new')
def new_issue_page():
    return get_template('new-issue.html').render()


@operator_route('POST', '/issues')
def create_issue_action():
    issue_id = create_issue(**get_http_arguments())
    return '/issues/{}'.format(issue_id)


@operator_route('GET', '/issues/{{ issue_id }}/edit', issue_id='\d+')
def update_issue_widget():
    return get_template('edit-issue.html').render(issue=get_issue(get_http_argument('issue_id')))


@operator_route('PUT', '/issues/{{ issue_id }}', issue_id='\d+')
def update_issue_action():
    update_issue(**get_http_arguments())
    return '/issues/{}'.format(get_http_argument('issue_id'))


@operator_route('POST', '/issues/{{ issue_id }}/materials/{{ category }}/choose', issue_id='\d+', category='\w+')
def choose_issue_materials_action():
    choose_issue_materials(**get_http_arguments())
