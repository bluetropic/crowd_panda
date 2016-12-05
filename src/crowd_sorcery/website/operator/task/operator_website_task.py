# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.task import *
from crowd_sorcery.feature.issue import *

operator_route = route_for('operator')


@operator_route('GET', '/issues/{{ issue_id }}/tasks/new', issue_id='\d+')
def new_issue_task_widget():
    return get_template('new-issue-task.html').render(issue_id=get_http_argument('issue_id'))


@operator_route('POST', '/issues/{{ issue_id }}/tasks', issue_id='\d+')
def create_issue_task_action():
    return create_issue_task(**get_http_arguments())


@operator_route('GET', '/issues/{{ issue_id }}/tasks', issue_id='\d+')
def list_issue_tasks_widget():
    issue_id = get_http_argument('issue_id')
    return get_template('list-issue-task.html').render(issue=get_issue(issue_id), tasks=list_issue_tasks(issue_id))


@operator_route('GET', '/issues/{{ issue_id }}/tasks/{{ task_id }}/edit', issue_id='\d+', task_id='\d+')
def update_issue_task_widget():
    return get_template('edit-issue-task.html').render(task=get_issue_task(**get_http_arguments()))


@operator_route('PUT', '/issues/{{ issue_id }}/tasks/{{ task_id }}', issue_id='\d+', task_id='\d+')
def update_issue_task_action():
    update_issue_task(**get_http_arguments())
    return '/issues/{}/tasks/{}'.format(get_http_argument('issue_id'), get_http_argument('task_id'))
