# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import timedelta
import logging

from decimal import Decimal
from veil.profile.model import *
from crowd_sorcery.feature.material import *

db = register_database('crowd_sorcery')
queue = register_queue()

TASK_RESULT_STATUS_WAITING_REVIEW = 1
TASK_RESULT_STATUS_REVIEW_ACCEPTED = 2
TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW = 3
TASK_RESULT_STATUS_REVIEW_REFUSED = 4
TASK_RESULT_STATUS_REVIEW_ACCEPTED_AFTER_OP_REVIEW = 5
TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW = 6

TASK_RESULT_STATUS = {
    TASK_RESULT_STATUS_WAITING_REVIEW: '等待评审',
    TASK_RESULT_STATUS_REVIEW_ACCEPTED: '评审接受',
    TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW: '等待裁定',
    TASK_RESULT_STATUS_REVIEW_REFUSED: '评审拒绝',
    TASK_RESULT_STATUS_REVIEW_ACCEPTED_AFTER_OP_REVIEW: '评审接受（裁决后）',
    TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW: '评审拒绝（裁决后）',
}

TASK_REFUSED_STATUS = tuple([TASK_RESULT_STATUS_REVIEW_REFUSED, TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW])
TASK_REFUSED_AND_WAIT_REVIEW_STATUS = tuple([TASK_RESULT_STATUS_WAITING_REVIEW, TASK_RESULT_STATUS_REVIEW_REFUSED,
    TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW])
ACCUMULATE_CREDIT_TASK_STATUS = {
    TASK_RESULT_STATUS_REVIEW_ACCEPTED, TASK_RESULT_STATUS_REVIEW_REFUSED, TASK_RESULT_STATUS_REVIEW_ACCEPTED_AFTER_OP_REVIEW,
    TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW
}

MAX_REVIEW_COUNT = 2

LOGGER = logging.getLogger(__name__)


def task_title_is_unique_in_issue(values):
    issue_id, title = values
    if db().exists('SELECT 1 FROM task WHERE issue_id=%(issue_id)s AND title=%(title)s', issue_id=issue_id, title=title):
        raise Invalid('Title has already used')
    return values


@command
def create_issue_task(issue_id=to_integer, title=(not_empty, clamp_length(max=64)), description=(not_empty, clamp_length(max=128)),
        max_material_for_each_gear=to_integer, max_material_process_interval=to_integer, credit_for_each_material=to_integer):
    return db().insert('task', returns_id=True, issue_id=issue_id, title=title, description=description,
        max_material_for_each_gear=max_material_for_each_gear,
        max_material_process_interval=timedelta(seconds=max_material_process_interval), credit_for_each_material=credit_for_each_material)


@command
def update_issue_task(issue_id=to_integer, task_id=to_integer, title=(not_empty, clamp_length(max=64)), description=(not_empty, clamp_length(max=128)),
        max_material_for_each_gear=to_integer, max_material_process_interval=to_integer, credit_for_each_material=to_integer):
    db().execute('''
        UPDATE task SET title=%(title)s, description=%(description)s, max_material_for_each_gear=%(max_material_for_each_gear)s,
            max_material_process_interval=%(max_material_process_interval)s, credit_for_each_material=%(credit_for_each_material)s
        WHERE id=%(task_id)s AND issue_id=%(issue_id)s
        ''', issue_id=issue_id, task_id=task_id, title=title, description=description,
                 max_material_process_interval=timedelta(seconds=max_material_process_interval),
                 max_material_for_each_gear=max_material_for_each_gear, credit_for_each_material=credit_for_each_material)


def list_issue_tasks(issue_id):
    return db().list('SELECT * FROM task WHERE issue_id=%(issue_id)s ORDER BY id', issue_id=issue_id)


def get_issue_task(issue_id, task_id):
    return db().get('SELECT * FROM task WHERE issue_id=%(issue_id)s AND id=%(task_id)s', issue_id=issue_id, task_id=task_id)


def list_tasks(gear_id=None):
    available_task_materials = db().list('''
        SELECT t.*, m.id AS material_id
        FROM task t
            INNER JOIN issue_material im ON im.issue_id=t.issue_id
            INNER JOIN material m ON m.id=im.material_id
            LEFT JOIN task_dispatch td ON td.task_id=t.id AND td.material_id=m.id
            LEFT JOIN (
                WITH DATA AS (
                    SELECT *, rank() over (partition by task_id, material_id order by id DESC) from task_result
                ) SELECT * FROM data WHERE rank=1
            ) tr ON tr.task_id=t.id AND tr.material_id=m.id
        WHERE tr.status IS NULL OR tr.status IN %(TASK_REFUSED_STATUS)s
    ''', TASK_REFUSED_STATUS=TASK_REFUSED_STATUS)
    task_id2available_materials = {}
    for row in available_task_materials:
        task_id2available_materials.setdefault(row.id, []).append(row)
    task_id2available_material_count = {task_id: len(materials) for task_id, materials in task_id2available_materials.items()}
    available_review_task_materials = db().list('SELECT * FROM task_result WHERE status=%(TASK_RESULT_STATUS_WAITING_REVIEW)s',
                                                TASK_RESULT_STATUS_WAITING_REVIEW=TASK_RESULT_STATUS_WAITING_REVIEW)
    if gear_id:
        available_review_task_materials = [m for m in available_review_task_materials if m.done_by != gear_id]
    task_id2available_review_materials = {}
    for row in available_review_task_materials:
        task_id2available_review_materials.setdefault(row.task_id, []).append(row)
    task_id2available_review_material_count = {task_id: len(materials) for task_id, materials in task_id2available_review_materials.items()}
    if gear_id:
        gear_processing_and_processed_materials = set(
            (row.task_id, row.material_id) for row in db().list('''
                SELECT task_id, material_id FROM task_result WHERE done_by=%(gear_id)s
                UNION
                SELECT task_id, material_id FROM task_dispatch WHERE gear_id=%(gear_id)s
                ''', gear_id=gear_id)
        )
        if gear_processing_and_processed_materials:
            for task_id, available_materials in task_id2available_materials.items():
                task_id2available_material_count[task_id] = len([m for m in available_materials if (task_id, m.material_id) not in gear_processing_and_processed_materials])
        gear_processing_and_processed_review_materials = set(
            (row.task_id, row.material_id) for row in db().list('''
                SELECT tr.task_id, tr.material_id FROM review_result rr INNER JOIN task_result tr ON tr.id=rr.result_id WHERE rr.reviewed_by=%(gear_id)s
                UNION
                SELECT tr.task_id, tr.material_id FROM review_dispatch rd INNER JOIN task_result tr ON tr.id=rd.result_id WHERE rd.reviewed_by=%(gear_id)s
                ''', gear_id=gear_id)
        )
        if gear_processing_and_processed_review_materials:
            for task_id, available_review_materials in task_id2available_review_materials.items():
                task_id2available_review_material_count[task_id] = len([rm for rm in available_review_materials if (task_id, rm.material_id) not in gear_processing_and_processed_review_materials])
    return [DictObject(available_material_count=task_id2available_material_count.get(task_id, 0),
                       available_review_material_count=task_id2available_review_material_count.get(task_id, 0),
                       **materials[0])
            for task_id, materials in task_id2available_materials.items()]


def list_gear_task_shards(gear_id, task_id=None):
    return db().list('''
        SELECT task_id, COUNT(*)
        FROM task_result
        WHERE done_at::DATE = CURRENT_DATE AND done_by=%(gear_id)s AND {task_id_term}
        GROUP BY task_id
        UNION ALL
        SELECT task_id, COUNT(*)
        FROM task_dispatch
        WHERE dispatched_at::DATE = CURRENT_DATE AND gear_id=%(gear_id)s AND {task_id_term}
        GROUP BY task_id
        '''.format(task_id_term='task_id=%(task_id)s' if task_id else 'TRUE'), gear_id=gear_id, task_id=task_id)


def list_gear_review_shards(gear_id):
    return db().list('''
        SELECT tr.task_id, COUNT(*) AS count
        FROM review_dispatch rd
            INNER JOIN task_result tr ON tr.id=rd.result_id
        WHERE rd.dispatched_at::DATE=CURRENT_DATE AND rd.reviewed_by=%(gear_id)s
        GROUP BY tr.task_id
        UNION ALL
        SELECT tr.task_id, COUNT(*) AS count
        FROM review_result rr
            INNER JOIN task_result tr ON tr.id=rr.result_id
        WHERE rr.reviewed_at::DATE=CURRENT_DATE AND rr.reviewed_by=%(gear_id)s
        GROUP BY tr.task_id
        ''', gear_id=gear_id)


@transactional(db)
@command
def create_task_application(gear_id=to_integer, task_id=to_integer):
    task_max_material_for_each_gear = db().get_scalar('SELECT max_material_for_each_gear FROM task WHERE id=%(task_id)s', task_id=task_id)
    gear_occupied_count = sum(r.count for r in list_gear_task_shards(gear_id, task_id=task_id))
    db().execute('''
        INSERT INTO task_dispatch(task_id, material_id, gear_id, expired_at)
        SELECT t.id, m.id, %(gear_id)s, CURRENT_TIMESTAMP+t.max_material_process_interval
        FROM task t
            INNER JOIN issue_material im ON im.issue_id=t.issue_id
            INNER JOIN material m on m.id=im.material_id
            LEFT JOIN task_dispatch td ON td.task_id=t.id AND td.material_id=m.id
            LEFT JOIN (
                WITH DATA AS (
                    SELECT *, rank() over (partition by task_id, material_id order by id DESC) from task_result
                ) SELECT * FROM data WHERE rank=1
            ) tr ON tr.task_id=t.id AND tr.material_id=m.id
        WHERE t.id=%(task_id)s AND (tr.status IS NULL OR tr.status IN %(TASK_REFUSED_STATUS)s) AND td.dispatched_at IS NULL
        FETCH FIRST %(row_count)s ROWS ONLY
        ''', task_id=task_id, gear_id=gear_id, TASK_REFUSED_STATUS=TASK_REFUSED_STATUS,
        row_count=min(task_max_material_for_each_gear, max(task_max_material_for_each_gear-gear_occupied_count, 0)))
    gear_occupied_count_after_applied = sum(r.count for r in list_gear_task_shards(gear_id, task_id=task_id))
    if gear_occupied_count_after_applied > task_max_material_for_each_gear:
        raise InvalidCommand({'@': 'Not available today'})


@transactional(db)
@command
def create_review_application(gear_id=to_integer, task_id=to_integer):
    task_max_material_for_each_gear = db().get_scalar('SELECT max_material_for_each_gear FROM task WHERE id=%(task_id)s', task_id=task_id)
    gear_occupied_count = db().get_scalar('''
        SELECT COALESCE(SUM(count), 0)
        FROM (
            SELECT COUNT(*)
            FROM review_dispatch rd
                INNER JOIN task_result tr ON tr.id=rd.result_id
            WHERE rd.dispatched_at::DATE=CURRENT_DATE AND rd.reviewed_by=%(gear_id)s AND tr.task_id=%(task_id)s
            UNION ALL
            SELECT COUNT(*)
            FROM review_result rr
                INNER JOIN task_result tr ON tr.id=rr.result_id
            WHERE rr.reviewed_at::DATE=CURRENT_DATE AND rr.reviewed_by=%(gear_id)s AND tr.task_id=%(task_id)s
        ) data
    ''', gear_id=gear_id, task_id=task_id)
    db().execute('''
        INSERT INTO review_dispatch(result_id, reviewed_by, expired_at)
        SELECT result_id, %(gear_id)s, CURRENT_TIMESTAMP + t.max_material_process_interval
        FROM (
            SELECT tr.id AS result_id
            FROM task_result tr
            LEFT JOIN (
                SELECT result_id, count(*)
                FROM review_dispatch
                WHERE CURRENT_TIMESTAMP<expired_at
                GROUP BY result_id
            ) rd ON rd.result_id=tr.id
            LEFT JOIN (
                SELECT result_id, count(*)
                FROM review_result
                GROUP BY result_id
            ) rc ON rc.result_id=tr.id
            WHERE tr.task_id=%(task_id)s AND status=%(TASK_RESULT_STATUS_WAITING_REVIEW)s AND COALESCE(rd.count, 0)<2 AND COALESCE(rc.count, 0)<2
            EXCEPT
            SELECT result_id
            FROM review_dispatch
            WHERE reviewed_by=%(gear_id)s
            EXCEPT
            SELECT result_id
            FROM review_result
            WHERE reviewed_by=%(gear_id)s
            ) r
            INNER JOIN task_result tr ON tr.id=r.result_id
            INNER JOIN task t ON t.id=tr.task_id
        FETCH FIRST %(row_count)s ROWS ONLY
        ''', task_id=task_id, gear_id=gear_id, TASK_REFUSED_STATUS=TASK_REFUSED_AND_WAIT_REVIEW_STATUS,
                 TASK_RESULT_STATUS_WAITING_REVIEW=TASK_RESULT_STATUS_WAITING_REVIEW,
                 row_count=min(task_max_material_for_each_gear, max(task_max_material_for_each_gear-gear_occupied_count, 0)))
    gear_occupied_count_after_applied = db().get_scalar('''
        SELECT COALESCE(SUM(count), 0)
        FROM (
            SELECT COUNT(*)
            FROM review_dispatch rd
                INNER JOIN task_result tr ON tr.id=rd.result_id
            WHERE rd.dispatched_at::DATE=CURRENT_DATE AND reviewed_by=%(gear_id)s AND task_id=%(task_id)s
            UNION ALL
            SELECT COUNT(*)
            FROM review_result rr
                INNER JOIN task_result tr ON tr.id=rr.result_id
            WHERE rr.reviewed_at::DATE=CURRENT_DATE AND reviewed_by=%(gear_id)s AND task_id=%(task_id)s
        ) data
    ''', gear_id=gear_id, task_id=task_id)
    if gear_occupied_count_after_applied > task_max_material_for_each_gear:
        raise InvalidCommand({'@': 'Not available today'})


def one_material_should_be_finished_by_one_gear_today(values):
    task_id, material_id, gear_id = values
    if db().exists('''
            SELECT 1 FROM task_result WHERE task_id=%(task_id)s AND material_id=%(material_id)s AND done_by=%(done_by)s AND done_at::DATE=CURRENT_DATE
            ''', task_id=task_id, material_id=material_id, done_by=gear_id):
        raise Invalid('Finished this material already')
    return values


@transactional(db)
@command({
    ('task_id', 'material_id', 'gear_id'): one_material_should_be_finished_by_one_gear_today
})
def create_task_result(task_id=to_integer, gear_id=to_integer, data=not_empty):
    for m in data:
        db().insert('task_result', task_id=task_id, material_id=m.material_id, done_by=gear_id, result=to_json(m.hotspots),
                    status=TASK_RESULT_STATUS_WAITING_REVIEW)


@periodic_job('*/10 * * * *')
def remove_expired_task_dispatch_job():
    db().execute("DELETE FROM task_dispatch WHERE CURRENT_TIMESTAMP-expired_at>=INTERVAL '1day'")


@periodic_job('*/1 * * * *')
def remove_expired_review_dispatch_job():
    db().execute('DELETE FROM review_dispatch WHERE CURRENT_TIMESTAMP>=expired_at')


def one_result_should_be_finished_by_one_gear_one_time(values):
    result_id, gear_id = values
    if db().exists('SELECT 1 FROM review_result WHERE result_id=%(result_id)s AND reviewed_by=%(reviewed_by)s', result_id=result_id, reviewed_by=gear_id):
        raise Invalid('Reviewed this material already')
    return values


@transactional(db)
@command({
    ('result_id', 'gear_id'): one_result_should_be_finished_by_one_gear_one_time
})
def create_task_review_result(result_id=to_integer, gear_id=to_integer, accept=to_bool):
    db().insert('review_result', result_id=result_id, reviewed_by=gear_id, is_accept=accept)
    update_task_result_status(result_id)


@transactional(db)
def update_task_result_status(result_id):
    review_results = db().list('SELECT * FROM review_result WHERE result_id=%(result_id)s', result_id=result_id)
    if len(review_results) < MAX_REVIEW_COUNT:
        return
    if len(set(result.is_accept for result in review_results)) == 1:
        if review_results[0].is_accept:
            status = TASK_RESULT_STATUS_REVIEW_ACCEPTED
        else:
            status = TASK_RESULT_STATUS_REVIEW_REFUSED
    else:
        status = TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW
    db().execute('UPDATE task_result SET status=%(status)s WHERE id=%(result_id)s', status=status, result_id=result_id)
    if status != TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW:
        queue().enqueue_after(accumulate_gear_credit_job, result_id=result_id)


@command
def update_task_result_status_by_op(id=to_integer, accept=to_bool):
    status = TASK_RESULT_STATUS_REVIEW_ACCEPTED_AFTER_OP_REVIEW if accept else TASK_RESULT_STATUS_REVIEW_REFUSED_AFTER_OP_REVIEW
    db().execute('UPDATE task_result SET status=%(status)s WHERE id=%(id)s AND status=%(TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW)s',
                 id=id, status=status, TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW=TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW)
    queue().enqueue_after(accumulate_gear_credit_job, result_id=id)


@job
def accumulate_gear_credit_job(result_id):
    task_result = db().get('SELECT tr.*, t.credit_for_each_material FROM task_result tr INNER JOIN task t ON t.id=tr.task_id WHERE tr.id=%(result_id)s',
                           result_id=result_id)
    if not task_result or task_result.status not in ACCUMULATE_CREDIT_TASK_STATUS:
        return
    if task_result.status in {TASK_RESULT_STATUS_REVIEW_ACCEPTED, TASK_RESULT_STATUS_REVIEW_ACCEPTED_AFTER_OP_REVIEW}:
        credit = task_result.credit_for_each_material
    else:
        credit = Decimal('-0.3') * task_result.credit_for_each_material
    db().execute('UPDATE gear SET credit=credit+%(credit)s WHERE id=%(gear_id)s', credit=credit, gear_id=task_result.done_by)
    db().insert('gear_credit_log', gear_id=task_result.done_by, credit=credit, comment='完成任务')


def list_gear_not_finished_materials(gear_id):
    materials = db().list('''
        SELECT td.task_id, td.expired_at, m.id, m.bucket_key
        FROM task_dispatch td
            INNER JOIN material m ON m.id=td.material_id
            LEFT JOIN (
                WITH DATA AS (
                    SELECT *, rank() over (partition by task_id, material_id order by id DESC) from task_result
                ) SELECT * FROM data WHERE rank=1
            ) tr ON tr.task_id=td.task_id AND tr.material_id=td.material_id
        WHERE gear_id=%(gear_id)s AND CURRENT_TIMESTAMP<td.expired_at AND (tr.id IS NULL OR tr.status IN %(TASK_REFUSED_STATUS)s OR tr.done_by!=%(gear_id)s)
        ''', gear_id=gear_id, TASK_REFUSED_STATUS=TASK_REFUSED_STATUS)
    for m in materials:
        m.url = get_material_image_url(m.bucket_key)
    return materials


def list_gear_not_finished_review(gear_id):
    materials = db().list('''
        SELECT tr.task_id, tr.result, rd.result_id, rd.expired_at, m.id, m.bucket_key
        FROM review_dispatch rd
            INNER JOIN task_result tr ON tr.id=rd.result_id
            INNER JOIN material m ON m.id=tr.material_id
            LEFT JOIN review_result rr ON rr.result_id=rd.result_id AND rr.reviewed_by=rd.reviewed_by
        WHERE rd.reviewed_by=%(gear_id)s AND CURRENT_TIMESTAMP<rd.expired_at AND rr.result_id IS NULL
        ''', gear_id=gear_id)
    for m in materials:
        m.url = get_material_image_url(m.bucket_key)
    return materials
