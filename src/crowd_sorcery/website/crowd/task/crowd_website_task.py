# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.task import *
from crowd_sorcery.feature.material import *
from crowd_sorcery.feature.gear import *

crowd_route = route_for('crowd')
crowd_public_route = route_for('crowd', tags=(TAG_NO_LOGIN_REQUIRED, ))


@crowd_public_route('GET', '/tasks')
def list_tasks_widget():
    gear_id = get_current_gear_id()
    current_gear = get_gear(gear_id)
    tasks = list_tasks(gear_id=gear_id)
    task_id2occupied = {}
    task_id2reviewed = {}
    gear_not_finished_task_ids = set()
    gear_not_reviewed_task_ids = set()
    if current_gear:
        for row in list_gear_task_shards(current_gear.id):
            if row.task_id not in task_id2occupied:
                task_id2occupied[row.task_id] = row.count
            else:
                task_id2occupied[row.task_id] += row.count
        for row in list_gear_review_shards(current_gear.id):
            if row.task_id not in task_id2reviewed:
                task_id2reviewed[row.task_id] = row.count
            else:
                task_id2reviewed[row.task_id] += row.count
        gear_not_finished_task_ids = set(t.task_id for t in list_gear_not_finished_materials(current_gear.id))
        gear_not_reviewed_task_ids = set(t.task_id for t in list_gear_not_finished_review(current_gear.id))

    for task in tasks:
        task.can_apply = task.available_material_count > 0 and task_id2occupied.get(task.id, 0) < task.max_material_for_each_gear
        task.can_apply_review = task.available_review_material_count > 0 and task_id2reviewed.get(task.id, 0) < task.max_material_for_each_gear
        task.have_not_finished = task.id in gear_not_finished_task_ids
        task.have_not_reviewed = task.id in gear_not_reviewed_task_ids

    return get_template('list-task.html').render(tasks=tasks, current_gear=current_gear)


@crowd_route('POST', '/tasks/{{ task_id }}/applications', task_id='\d+')
def create_task_application_action():
    create_task_application(get_current_gear_id(), get_http_argument('task_id'))


@crowd_route('POST', '/tasks/{{ task_id }}/review-applications', task_id='\d+')
def create_task_application_action():
    create_review_application(gear_id=get_current_gear_id(), **get_http_arguments())


@crowd_route('GET', '/issues/{{ issue_id }}/tasks/{{ task_id }}', issue_id='\d+', task_id='\d+')
def task_show_page():
    return get_template('task-show.html').render(task=get_issue_task(get_http_argument('issue_id'), get_http_argument('task_id')),
        not_finished_materials=list_gear_not_finished_materials(get_current_gear_id()))


@crowd_route('POST', '/tasks/{{ task_id }}/results', task_id='\d+')
def create_task_result_action():
    arguments = get_http_arguments()
    arguments.gear_id = get_current_gear_id()
    create_task_result(**arguments)


@crowd_route('GET', '/issues/{{ issue_id }}/tasks/{{ task_id }}/reviews', issue_id='\d+', task_id='\d+')
def review_show_page():
    return get_template('review-show.html').render(task=get_issue_task(get_http_argument('issue_id'), get_http_argument('task_id')),
        not_reviewed_materials=list_gear_not_finished_review(get_current_gear_id()))


@crowd_route('POST', '/tasks/{{ task_id }}/review-results', task_id='\d+')
def create_task_review_result_action():
    arguments = get_http_arguments()
    arguments.pop('task_id')
    arguments.gear_id = get_current_gear_id()
    create_task_review_result(**arguments)