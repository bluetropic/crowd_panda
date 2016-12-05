# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from uuid import uuid4
from veil.profile.model import *
from veil.utility.hash import *
from veil.frontend.visitor import *
from veil.frontend.cli import *


db = register_database('crowd_sorcery')

LOGGER = logging.getLogger(__name__)


@command
def operator_login(username=not_empty, password=not_empty):
    operator = get_operator_by_username_and_password(username, password)
    if not operator:
        raise InvalidCredential('Invalid Username or password')
    remember_current_signed_in_operator(operator)


def remember_current_signed_in_operator(operator):
    remember_logged_in_user_id(operator.id)


def remove_current_signed_in_operator():
    remove_logged_in_user_id('operator')


def get_operator_by_username_and_password(username, password):
    return db().get('SELECT * FROM operator WHERE username=%(username)s AND password=%(password)s AND active', username=username,
        password=get_password_hash(password))


def get_current_operator_id():
    operator_id = get_logged_in_user_id('operator')
    return int(operator_id) if operator_id else None


def get_operator(operator_id):
    return db().get('SELECT * FROM operator WHERE id=%(id)s', id=operator_id)


def get_current_operator():
    current_operator_id = get_current_operator_id()
    return get_operator(current_operator_id) if current_operator_id else None


@script('create')
def create_operator_script(name, email, username):
    if not is_email(email, return_none_when_invalid=True):
        print('请输入格式正确的邮箱地址')
        return
    if db().exists('SELECT 1 FROM operator WHERE email=%(email)s OR username=%(username)s FETCH FIRST ROW ONLY', email=email, username=username):
        print('邮箱或用户名重复')
        return
    password = uuid4().get_hex()[:8]
    db().insert('operator', name=name, email=email, username=username, password=get_password_hash(password))
    # TODO: verify email and set password during verification
    print('请使用用户名：{}，密码：{} 登陆'.format(username, password))


class InvalidCredential(Exception):
    pass