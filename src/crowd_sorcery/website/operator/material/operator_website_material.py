# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from crowd_sorcery.feature.issue import *
from crowd_sorcery.feature.material import *

operator_route = route_for('operator')


@operator_route('GET', '/issues/{{ issue_id }}/materials', issue_id='\d+')
@widget
def list_issue_materials_widget(issue_id=None):
    issue_id = issue_id or get_http_argument('issue_id')
    return get_template('list-issue-materials.html').render(issue=get_issue(issue_id), materials=list_issue_materials(issue_id))


@widget
def list_material_categories_widget(issue_id):
    return get_template('list-material-categories.html').render(categories=list_material_categories(issue_id), issue_id=issue_id)


@operator_route('GET', '/materials/{{ category }}/images', category='\w+')
@widget
def list_materials_widget():
    category = get_http_argument('category')
    return get_template('list-materials.html').render(materials=list_category_materials(category), category=category)
