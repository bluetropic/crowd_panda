# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.frontend.visitor import *
from veil.profile.model import *
from veil.utility.hash import *

db = register_database('crowd_sorcery')


def email_is_unique(email):
    if db().exists('SELECT 1 FROM gear WHERE email=%(email)s', email=email):
        raise Invalid('Email already used')
    return email


def username_is_unique(username):
    if db().exists('SELECT 1 FROM gear WHERE username=%(username)s', username=username):
        raise Invalid('Username already used')
    return username


def password_and_confirm_check(values):
    p, p1 = values
    if p != p1:
        raise Invalid('password and password confirm should be equal')
    return values


@command({
    ('password', 'password_confirm'): password_and_confirm_check
})
def create_gear(name=not_empty, email=(is_email, email_is_unique), username=(not_empty, username_is_unique), password=not_empty,
        password_confirm=not_empty):
    gear_id = db().insert('gear', returns_id=True, name=name, email=email, username=username, password=get_password_hash(password))
    remember_current_signed_in_gear(gear_id)
    return gear_id


def remember_current_signed_in_gear(gear_id):
    remember_logged_in_user_id(gear_id)
    

def remove_current_signed_in_gear():
    remove_logged_in_user_id('crowd')


def get_gear_by_username_and_password(username, password):
    return db().get('SELECT * FROM gear WHERE username=%(username)s AND password=%(password)s', username=username,
        password=get_password_hash(password))


def get_current_gear_id():
    gear_id = get_logged_in_user_id('crowd')
    return int(gear_id) if gear_id else None


def get_gear(gear_id):
    return db().get('SELECT * FROM gear WHERE id=%(id)s', id=gear_id)


def get_current_gear():
    current_gear_id = get_current_gear_id()
    return get_gear(current_gear_id) if current_gear_id else None


@command
def gear_signin(username=not_empty, password=not_empty):
    gear = get_gear_by_username_and_password(username, password)
    if not gear:
        raise InvalidCredential('Invalid Username or password')
    remember_current_signed_in_gear(gear.id)


class InvalidCredential(Exception):
    pass


def list_not_activated_gears():
    return db().list('SELECT * FROM gear WHERE NOT active')


@command
def activate_gear(gear_id=to_integer):
    db().execute('UPDATE gear SET active=TRUE WHERE NOT active AND id=%(gear_id)s', gear_id=gear_id)


def list_gear_credit_logs(gear_id):
    return db().list('SELECT * FROM gear_credit_log WHERE gear_id=%(gear_id)s ORDER BY accumulated_at DESC, id DESC', gear_id=gear_id)
