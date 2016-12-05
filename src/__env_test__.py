from __future__ import unicode_literals, print_function, division
from veil_component import *
from veil.profile.setting import *
import __env__

TEST_SUPERVISOR_HTTP_PORT = 9091
TEST_REDIS_HOST = '127.0.0.1'
TEST_REDIS_PORT = 6380

config = __env__.env_config(
    crowd_website_start_port=2050,
    crowd_website_process_count=1,
    crowd_website_domain='crowd.cs.dev.dmright.com',
    crowd_website_domain_port=81,
    operator_website_start_port=2060,
    operator_website_process_count=1,
    operator_website_domain='operator.cs.dev.dmright.com',
    operator_website_domain_port=81,
    crowd_sorcery_postgresql_version='9.5',
    crowd_sorcery_postgresql_host='127.0.0.1',
    crowd_sorcery_postgresql_port=6544,
    crowd_sorcery_postgresql_enable_chinese_fts=True,
    queue_type='immediate',
    queue_host='', # no queue
    queue_port=0,
    resweb_domain='', # no resweb
    resweb_domain_port=0,
    resweb_host='',
    resweb_port=0,
    persist_store_redis_host=TEST_REDIS_HOST,
    persist_store_redis_port=TEST_REDIS_PORT,
    memory_cache_redis_host=TEST_REDIS_HOST,
    memory_cache_redis_port=TEST_REDIS_PORT
)

ENV_TEST = {
    'test': veil_env(name='test', hosts={}, servers={
        '@': veil_server(
            host_name='',
            sequence_no=20,
            supervisor_http_port=TEST_SUPERVISOR_HTTP_PORT,
            programs=merge_multiple_settings(
                redis_program('test', TEST_REDIS_HOST, TEST_REDIS_PORT),
                __env__.crowd_sorcery_postgresql_program(config),
                __env__.log_rotated_nginx_program(merge_multiple_settings(
                    __env__.crowd_website_nginx_server(config),
                    __env__.operator_website_nginx_server(config),
                ))
            ),
            resources=[application_resource(component_names=list_all_components(), config=merge_settings(
                __env__.crowd_sorcery_config(config), {
                    'test_bucket': {
                        'type': 'filesystem',
                        'base_directory': '',
                        'base_url': ''
                    }
                }
            ))]
        )
    })
}
