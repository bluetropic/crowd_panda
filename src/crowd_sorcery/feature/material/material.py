# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging

from veil.utility.pillow import *
from veil_component import as_path
from veil.frontend.cli import script
from veil.profile.model import *

db = register_database('crowd_sorcery')
queue = register_queue()
bucket = register_bucket('material')

LOGGER = logging.getLogger(__name__)


def list_material_categories(issue_id):
    categories = db().list('SELECT DISTINCT category FROM material')
    chosen_categories = db().list_scalar('''
        SELECT DISTINCT category
        FROM issue_material im
            INNER JOIN material m ON m.id=im.material_id
        WHERE im.issue_id=%(issue_id)s
        ''', issue_id=issue_id)
    for c in categories:
        c.chosen = c.category in chosen_categories
    return categories


def list_category_materials(category):
    materials = db().list('SELECT * FROM material WHERE category=%(category)s', category=category)
    for m in materials:
        m.url = bucket().get_url(m.bucket_key)
    return materials


def list_issue_materials(issue_id):
    materials = db().list('''
        SELECT *
        FROM issue_material im
            INNER JOIN material m ON m.id=im.material_id
        WHERE im.issue_id=%(issue_id)s
        ORDER BY m.id DESC
        ''', issue_id=issue_id)
    for m in materials:
        m.url = bucket().get_url(m.bucket_key)
    return materials


def list_issue_task_materials(issue_id, task_id):
    materials = db().list('''
        SELECT *
        FROM material
        WHERE issue_id=%(issue_id)s AND task_id=%(task_id)s AND NOT deleted
        ORDER BY id DESC
        FETCH FIRST 10 ROWS ONLY
        ''', issue_id=issue_id, task_id=task_id)
    for m in materials:
        m.url = bucket().get_url(m.bucket_key)
    return materials


def material_is_not_using(material_id):
    material = db().get('SELECT * FROM material WHERE id=%(material_id)s', material_id=material_id)
    if not material:
        raise Invalid('Invalid material')
    if db().exists('''
            SELECT 1
            FROM task_dispatch td
                INNER JOIN material m ON m.id=td.material_id
            WHERE m.hash=%(material_hash)s AND m.bucket_key=%(material_bucket_key)s
            UNION
            SELECT 1
            FROM task_result tr
                INNER JOIN material m ON m.id=tr.material_id
            WHERE m.hash=%(material_hash)s AND m.bucket_key=%(material_bucket_key)s
            ''', material_hash=material.hash, material_bucket_key=material.bucket_key):
        raise Invalid('Material is using')
    return material_id


@script('import')
def import_material_script(path):
    for d in as_path(path).walkdirs():
        dir_name = d.basename()
        for f in d.walkfiles():
            file_name = f.basename()
            bucket_key = '{}/{}'.format(dir_name, file_name)
            save_image(f, bucket, bucket_key)
            db().insert('material', category=dir_name, bucket_key=bucket_key)


def get_material_image_url(bucket_key):
    return bucket().get_url(bucket_key)
