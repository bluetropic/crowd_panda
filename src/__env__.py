from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.profile.setting import *
from veil.frontend.nginx_setting import NGINX_PID_PATH

HTTP_SCHEME = 'http'
HTTPS_SCHEME = 'https'
HTTP_STANDARD_PORT = 80
HTTPS_STANDARD_PORT = 443

WEBSITES = ['crowd', 'operator']

CROWD_WEBSITE_BUCKETS = ['captcha_image', 'material']
OPERATOR_WEBSITE_BUCKETS = []

OPERATOR_WEBSITE_MAX_UPLOAD_FILE_SIZE = '10m'

REDIS_CLIENTS = ['persist_store', 'memory_cache']

WEB_SERVICES = []

POSTGRESQL_CLIENTS = ['crowd_sorcery']

SECURITY_CONFIG = load_config_from(
    SECURITY_CONFIG_FILE,
    'crowd_db_user',  # this application database user name, use 'veil' in development machine
    'crowd_db_password',  # this application database user password, use 'p@55word' in development machine
    'crowd_db_owner',
    'crowd_db_owner_password',
    'hash_salt'  # used to hash password and secure cookie
)

LOGGING_LEVEL_CONFIG = objectify({
    'delayed_job_scheduler': 'info',
    'job_worker': 'info', # just control how pyres do the logging, our code still controlled by LOGGING_LEVEL_CONFIG.crowd_sorcery
    'crowd_sorcery_postgresql': {
        'log_min_duration_statement': 0 if VEIL_ENV_TYPE == 'development' else 300
    },
    'crowd_sorcery': {
        '__default__': 'DEBUG' if VEIL_ENV_TYPE in {'development', 'test'} else 'INFO',
#        'crowd_sorcery.feature': 'DEBUG',
    }
})


def env_config(
        crowd_website_start_port, crowd_website_process_count,
        crowd_website_domain, crowd_website_domain_port,
        operator_website_start_port, operator_website_process_count,
        operator_website_domain, operator_website_domain_port,
        persist_store_redis_host, persist_store_redis_port,
        memory_cache_redis_host, memory_cache_redis_port,
        crowd_sorcery_postgresql_version, crowd_sorcery_postgresql_host, crowd_sorcery_postgresql_port, crowd_sorcery_postgresql_enable_chinese_fts,
        queue_type, queue_host, queue_port,
        resweb_domain, resweb_domain_port,
        resweb_host, resweb_port):
    return objectify(locals())


_resweb_program = resweb_program


def resweb_program(config):
    return _resweb_program(config.resweb_host, config.resweb_port, config.queue_host, config.queue_port)


def resweb_nginx_server(config):
    return nginx_server(config.resweb_domain, config.resweb_domain_port, {'/': nginx_reverse_proxy_location(config.resweb_host, config.resweb_port)})


_queue_program = queue_program


def queue_program(config):
    return _queue_program(config.queue_host, config.queue_port)


_delayed_job_scheduler_program = delayed_job_scheduler_program


def delayed_job_scheduler_program(config):
    return _delayed_job_scheduler_program(
        config.queue_host, config.queue_port,
        logging_level=LOGGING_LEVEL_CONFIG.delayed_job_scheduler)


def crowd_sorcery_periodic_job_scheduler_program(config):
    return periodic_job_scheduler_program(LOGGING_LEVEL_CONFIG.crowd_sorcery, application_config=crowd_sorcery_config(config))


def crowd_sorcery_job_worker_program(worker_name, queue_names, config, run_as=None, count=1, timeout=180):
    return job_worker_program(worker_name,
        LOGGING_LEVEL_CONFIG.job_worker, LOGGING_LEVEL_CONFIG.crowd_sorcery,
        config.queue_host, config.queue_port, queue_names=queue_names,
        application_config=crowd_sorcery_config(config),
        run_as=run_as, count=count, timeout=timeout)


def transactional_email_worker_program(config, count=1):
    return crowd_sorcery_job_worker_program('transactional_email', ['send_transactional_email'], config, count=count)


def transactional_sms_worker_program(config, count=1):
    return crowd_sorcery_job_worker_program('transactional_sms', ['send_transactional_sms'], config, count=count)


def task_routine_worker_program(config, count=2):
    return crowd_sorcery_job_worker_program('task_routine', [
        'remove_expired_task_dispatch',
        'remove_expired_review_dispatch',
        'delete_material',
    ], config, count=count)


def postgresql_log_rotater_program(purpose):
    return log_rotater_program('{}_postgresql'.format(purpose), '* * * * *', {
        VEIL_LOG_DIR / '{}-postgresql'.format(purpose) / '*.csv': [
            'rotate 5',
            'size=50M',
            'missingok',
            'copytruncate'
        ]
    })


def log_rotated_postgresql_program(purpose, *args, **kwargs):
    if VEIL_ENV_TYPE != 'development':
        kwargs['log_filename'] = 'postgresql.log' # will disable the builtin log rotation
    return merge_multiple_settings(
        postgresql_program(purpose, *args, **kwargs),
        postgresql_log_rotater_program(purpose))


def crowd_sorcery_postgresql_program(config, more_config=None):
    more_config = more_config or {}
    return log_rotated_postgresql_program(
        'crowd_sorcery',
        config.crowd_sorcery_postgresql_version, config.crowd_sorcery_postgresql_host, config.crowd_sorcery_postgresql_port,
        owner=SECURITY_CONFIG.crowd_db_owner,
        owner_password=SECURITY_CONFIG.crowd_db_owner_password,
        user=SECURITY_CONFIG.crowd_db_user,
        password=SECURITY_CONFIG.crowd_db_password,
        log_min_duration_statement=LOGGING_LEVEL_CONFIG.crowd_sorcery_postgresql.log_min_duration_statement,
        enable_chinese_fts=config.crowd_sorcery_postgresql_enable_chinese_fts,
        **more_config)


def persist_store_redis_program(config):
    return redis_program('persist_store', config.persist_store_redis_host, config.persist_store_redis_port, persisted_by_aof=True)


def memory_cache_redis_program(config):
    return redis_program('memory_cache', config.memory_cache_redis_host, config.memory_cache_redis_port)


def crowd_website_programs(config):
    return website_programs('crowd', LOGGING_LEVEL_CONFIG.crowd_sorcery, application_config=crowd_sorcery_config(config),
        start_port=config.crowd_website_start_port, process_count=config.crowd_website_process_count)


def crowd_website_nginx_server(config, extra_locations=None):
    locations = website_locations('crowd')
    locations = merge_multiple_settings(locations, extra_locations or {}, website_bucket_locations(CROWD_WEBSITE_BUCKETS))
    return nginx_server(config.crowd_website_domain, config.crowd_website_domain_port, locations=locations,
        upstreams=website_upstreams('crowd', config.crowd_website_start_port, config.crowd_website_process_count),
        error_page={'404': '404.html', '500': '500.html'}, error_page_dir='{}/static/error-page'.format(VEIL_HOME))


def operator_website_programs(config):
    return website_programs('operator', LOGGING_LEVEL_CONFIG.crowd_sorcery, application_config=crowd_sorcery_config(config),
        start_port=config.operator_website_start_port, process_count=config.operator_website_process_count)


def operator_website_nginx_server(config, **nginx_config):
    if VEIL_ENV_TYPE in {'public', 'staging'}:
        extra_headers = ('add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";',)
    else:
        extra_headers = ()
    locations = website_locations('operator', max_upload_file_size=OPERATOR_WEBSITE_MAX_UPLOAD_FILE_SIZE, extra_headers=extra_headers)
    locations = merge_multiple_settings(locations, website_bucket_locations(OPERATOR_WEBSITE_BUCKETS))
    return nginx_server(config.operator_website_domain, config.operator_website_domain_port, locations=locations,
        upstreams=website_upstreams('operator', config.operator_website_start_port, config.operator_website_process_count),
        error_page={'404': '404.html', '500': '500.html'}, error_page_dir='{}/static/error-page'.format(VEIL_HOME), **nginx_config)


def nginx_log_rotater_program():
    return log_rotater_program('nginx', '* * * * *', {
        VEIL_LOG_DIR / 'nginx' / '*.log': [
            'rotate 5',
            'size=50M',
            'missingok',
            'notifempty',
            'sharedscripts',
            'postrotate',
            'if [ -f {} ]; then'.format(NGINX_PID_PATH),
            'kill -USR1 `cat {}`'.format(NGINX_PID_PATH),
            'fi',
            'endscript'
        ]
    })


def log_rotated_nginx_program(*args, **kwargs):
    return merge_multiple_settings(nginx_program(*args, **kwargs), nginx_log_rotater_program())


def crowd_sorcery_config(config):
    crowd_sorcery_config_ = objectify({
        'queue_client': {
            'type': config.queue_type,
            'host': config.queue_host,
            'port': config.queue_port
        },
        'hash': {
            'salt': SECURITY_CONFIG.hash_salt
        },
        'sendgrid_client': {
            'username': SECURITY_CONFIG.sendgrid_username,
            'password': SECURITY_CONFIG.sendgrid_password
        },
    })
    for purpose in REDIS_CLIENTS:
        crowd_sorcery_config_['{}_redis_client'.format(purpose)] = {
            'host': config['{}_redis_host'.format(purpose)],
            'port': config['{}_redis_port'.format(purpose)]
        }
    crowd_website_authority = config.crowd_website_domain if 80 == config.crowd_website_domain_port else '{}:{}'.format(config.crowd_website_domain, config.crowd_website_domain_port)
    for purpose in CROWD_WEBSITE_BUCKETS:
        crowd_sorcery_config_['{}_bucket'.format(purpose)] = {
            'type': 'filesystem',
            'base_directory': VEIL_BUCKETS_DIR / purpose.replace('_', '-'),
            'base_url': 'http://{}/buckets/{}'.format(crowd_website_authority, purpose.replace('_', '-')),
        }
    operator_website_authority = config.operator_website_domain if 80 == config.operator_website_domain_port else '{}:{}'.format(config.operator_website_domain, config.operator_website_domain_port)
    for purpose in OPERATOR_WEBSITE_BUCKETS:
        crowd_sorcery_config_['{}_bucket'.format(purpose)] = {
            'type': 'filesystem',
            'base_directory': VEIL_BUCKETS_DIR / purpose.replace('_', '-'),
            'base_url': '{}://{}/buckets/{}'.format('http' if VEIL_ENV_TYPE in {'development', 'test'} else 'https', operator_website_authority, purpose.replace('_', '-')),
        }
    for purpose in WEB_SERVICES:
        crowd_sorcery_config_['{}_web_service'.format(purpose)] = {
            'url': config['{}_web_service_url'.format(purpose)],
            'user': SECURITY_CONFIG.get('{}_web_service_user'.format(purpose), ''),
            'password': SECURITY_CONFIG.get('{}_web_service_password'.format(purpose), ''),
            'proxy_netloc': config['{}_web_service_proxy_netloc'.format(purpose)]
        }
    for purpose in POSTGRESQL_CLIENTS:
        crowd_sorcery_config_['{}_database_client'.format(purpose)] = {
            'driver': 'veil.backend.database.postgresql',
            'type': 'postgresql',
            'host': config['{}_postgresql_host'.format(purpose)],
            'port': config['{}_postgresql_port'.format(purpose)],
            'database': purpose,
            'enable_chinese_fts': config['{}_postgresql_enable_chinese_fts'.format(purpose)],
            'user': SECURITY_CONFIG.crowd_db_user,
            'password': SECURITY_CONFIG.crowd_db_password,
            'schema': 'public'
        }
    for website in WEBSITES:
        if isinstance(website, dict):
            purpose = website.purpose
            crowd_sorcery_config_['{}_website'.format(purpose)] = {
                'domain': config['{}_website_domain'.format(purpose)],
                'domain_port': config['{}_website_domain_port'.format(purpose)],
                'domain_scheme': config.get('{}_website_domain_scheme'.format(purpose), HTTPS_SCHEME if config['{}_website_domain_port'.format(purpose)] == HTTPS_STANDARD_PORT else HTTP_SCHEME),
                'start_port': config['{}_website_start_port'.format(purpose)],
                'locale': 'zh_Hans_CN.UTF-8',
                'master_template_directory': VEIL_HOME / 'src' / 'crowd_sorcery' / 'website' / purpose,
                'prevents_xsrf': website.prevents_xsrf,
                'recalculates_static_file_hash': website.recalculates_static_file_hash,
                'process_page_javascript': True,
                'process_page_stylesheet': True,
                'clears_template_cache': website.clears_template_cache
            }
        else:
            purpose = website
            crowd_sorcery_config_['{}_website'.format(purpose)] = {
                'domain': config['{}_website_domain'.format(purpose)],
                'domain_port': config['{}_website_domain_port'.format(purpose)],
                'domain_scheme': config.get('{}_website_domain_scheme'.format(purpose), HTTPS_SCHEME if config['{}_website_domain_port'.format(purpose)] == HTTPS_STANDARD_PORT else HTTP_SCHEME),
                'start_port': config['{}_website_start_port'.format(purpose)],
                'locale': 'zh_Hans_CN.UTF-8',
                'master_template_directory': VEIL_HOME / 'src' / 'crowd_sorcery' / 'website' / purpose,
                'prevents_xsrf': True,
                'recalculates_static_file_hash': True,
                'process_page_javascript': True,
                'process_page_stylesheet': True,
                'clears_template_cache': True
            }
    return crowd_sorcery_config_


def website_bucket_locations(purposes, valid_referer_domains=None):
    locations = {}
    for purpose in purposes:
        bucket_base_directory = VEIL_BUCKETS_DIR / purpose.replace('_', '-')
        location = bucket_location(bucket_base_directory, valid_referer_domains)
        locations.update({
            '^~ /buckets/{}/'.format(purpose.replace('_', '-')): location
        })
    return locations
