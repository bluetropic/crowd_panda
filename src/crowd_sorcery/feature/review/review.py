# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.model import *
from crowd_sorcery.feature.task import *
from crowd_sorcery.feature.material import *

db = register_database('crowd_sorcery')


def list_waiting_for_operator_reviews():
    reviews = db().list('''
        SELECT tr.*, m.bucket_key, g.name AS gear_name
        FROM task_result tr
            INNER JOIN material m ON m.id=tr.material_id
            INNER JOIN gear g ON g.id=tr.done_by
        WHERE tr.status=%(TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW)s
        ''', TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW=TASK_RESULT_STATUS_WAITING_OPERATOR_REVIEW)
    for review in reviews:
        review.url = get_material_image_url(review.bucket_key)
    return reviews
