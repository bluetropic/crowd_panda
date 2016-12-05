# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.model import *
from crowd_sorcery.feature.material import *

db = register_database('crowd_sorcery')


def list_issues():
    return db().list('SELECT * FROM issue ORDER BY id')


@command
def create_issue(title=(not_empty, clamp_length(max=64)), description=(not_empty, clamp_length(max=100))):
    return db().insert('issue', returns_id=True, title=title, description=description)


def get_issue(issue_id):
    return db().get('SELECT * FROM issue WHERE id=%(issue_id)s', issue_id=issue_id)


@command
def update_issue(issue_id=to_integer, title=(not_empty, clamp_length(max=64)), description=(not_empty, clamp_length(max=100))):
    db().execute('UPDATE issue SET title=%(title)s, description=%(description)s WHERE id=%(issue_id)s', issue_id=issue_id, title=title, description=description)


@command
def choose_issue_materials(issue_id=to_integer, category=not_empty):
    materials = list_category_materials(category)
    db().insert('issue_material', materials, issue_id=issue_id, material_id=lambda m: m.id, include_attributes=())
