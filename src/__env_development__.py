from __future__ import unicode_literals, print_function, division
from veil.profile.setting import *
import __env__

DEVELOPMENT_SUPERVISOR_HTTP_PORT = 9090
DEVELOPMENT_REDIS_HOST = '127.0.0.1'
DEVELOPMENT_REDIS_PORT = 6379

config = __env__.env_config(
    crowd_website_start_port=2000,
    crowd_website_process_count=1,
    crowd_website_domain='crowd.cs.dev.dmright.com',
    crowd_website_domain_port=80,
    operator_website_start_port=2010,
    operator_website_process_count=1,
    operator_website_domain='operator.cs.dev.dmright.com',
    operator_website_domain_port=80,
    queue_type='redis',
    queue_host=DEVELOPMENT_REDIS_HOST,
    queue_port=DEVELOPMENT_REDIS_PORT,
    resweb_domain='queue.cs.dev.dmright.com',
    resweb_domain_port=80,
    resweb_host='127.0.0.1',
    resweb_port=7070,
    persist_store_redis_host=DEVELOPMENT_REDIS_HOST,
    persist_store_redis_port=DEVELOPMENT_REDIS_PORT,
    memory_cache_redis_host=DEVELOPMENT_REDIS_HOST,
    memory_cache_redis_port=DEVELOPMENT_REDIS_PORT,
    crowd_sorcery_postgresql_version='9.5',
    crowd_sorcery_postgresql_host='127.0.0.1',
    crowd_sorcery_postgresql_port=6543,
    crowd_sorcery_postgresql_enable_chinese_fts=False
)
ENV_DEVELOPMENT = {
    'development': veil_env(name='development', hosts={}, servers={
        '@': veil_server(
            host_name='',
            sequence_no=10,
            supervisor_http_port=DEVELOPMENT_SUPERVISOR_HTTP_PORT,
            programs=merge_multiple_settings(
                redis_program('development', DEVELOPMENT_REDIS_HOST, DEVELOPMENT_REDIS_PORT),
                __env__.crowd_sorcery_postgresql_program(config),
                __env__.resweb_program(config),
                __env__.delayed_job_scheduler_program(config),
                __env__.crowd_sorcery_periodic_job_scheduler_program(config),
                __env__.crowd_sorcery_job_worker_program(
                    worker_name='development',
                    queue_names=[
                        'clean_up_captcha_images',
                        'clean_up_inline_static_files',
                        'remove_expired_task_dispatch',
                        'remove_expired_review_dispatch',
                        'delete_material',
                        'accumulate_gear_credit',
                    ],
                    config=config, count=2),
                __env__.crowd_website_programs(config),
                __env__.operator_website_programs(config),
                __env__.log_rotated_nginx_program(merge_multiple_settings(
                    __env__.resweb_nginx_server(config),
                    __env__.crowd_website_nginx_server(config),
                    __env__.operator_website_nginx_server(config),
                ))
            )
        )
    })
}
