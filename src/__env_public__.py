from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.profile.setting import *
import __env__

LOG_REDIS_PORT = 5140

EXTERNAL_NIC = 'eth0'


def crowd_sorcery_public_servers(host_name, lan_range, crowd_website_domain, operator_website_domain, is_production=True):
    worker_ip = '{}.20'.format(lan_range)
    db_ip = '{}.30'.format(lan_range)
    monitor_ip = '{}.98'.format(lan_range)

    postgresql_log_collector_config = {'host': monitor_ip, 'port': LOG_REDIS_PORT, 'key': 'postgresql'}
    json_event_log_collector_config = {'host': monitor_ip, 'port': LOG_REDIS_PORT, 'key': 'json_event'}
    config = __env__.env_config(
            crowd_website_start_port=5000,
            crowd_website_process_count=4,
            crowd_website_domain=crowd_website_domain,
            crowd_website_domain_port=80,
            operator_website_start_port=5100,
            operator_website_process_count=2,
            operator_website_domain=operator_website_domain,
            operator_website_domain_port=443,
            queue_type='redis',
            queue_host=db_ip,
            queue_port=6378,
            resweb_domain='',  # do not expose it to public
            resweb_domain_port=0,  # do not expose it to public
            resweb_host=worker_ip,
            resweb_port=7070,
            persist_store_redis_host=db_ip,
            persist_store_redis_port=6381,
            memory_cache_redis_host=db_ip,
            memory_cache_redis_port=6382,
            crowd_sorcery_postgresql_version='9.4',
            crowd_sorcery_postgresql_host=db_ip,
            crowd_sorcery_postgresql_port=5432,
            crowd_sorcery_postgresql_enable_chinese_fts=False
    )
    cw_postgresql_more_config = DictObject(
            shared_buffers='1GB',
            work_mem='16MB',
            maintenance_work_mem='64MB',
            effective_io_concurrency=3,
            checkpoint_completion_target=0.9,
            effective_cache_size='1GB') if is_production else DictObject()
    crowd_website_authority = config.crowd_website_domain if 80 == config.crowd_website_domain_port else '{}:{}'.format(
        config.crowd_website_domain, config.crowd_website_domain_port)

    config.redis_servers = [(config.queue_host, config.queue_port), (config.persist_store_redis_host, config.persist_store_redis_port),
                            (config.memory_cache_redis_host, config.memory_cache_redis_port)]

    return ['web', 'worker', 'db'], {
        'web': veil_server(
                host_name=host_name,
                sequence_no=10,
                mount_editorial_dir=False,
                mount_buckets_dir=True,
                programs=merge_multiple_settings(
                        __env__.crowd_website_programs(config),
                        __env__.operator_website_programs(config),
                        __env__.log_rotated_nginx_program(merge_multiple_settings(
                                __env__.operator_website_nginx_server(config, keepalive_timeout='120', ssl=True, ssl_session_timeout='15m',
                                                                      ssl_certificate='/etc/ssl/certs/op.tgcaem.org.fullchain.pem',
                                                                      ssl_certificate_key='/etc/ssl/private/op.tgcaem.org.privkey.pem'),
                                __env__.crowd_website_nginx_server(config),
                                nginx_server('_', config.crowd_website_domain_port, locations={},
                                             rewrite='^ http://{}/'.format(crowd_website_authority), default_server=True)
                        ),
                                enable_compression=True,
                                worker_process_count='auto' if is_production else 2, worker_priority=-5, worker_rlimit_nofile=130000, worker_connections=2048),
                ),
                ssh_port=22
        ),
        'worker': veil_server(
                host_name=host_name,
                sequence_no=20,
                mount_buckets_dir=True,
                programs=merge_multiple_settings(
                        __env__.resweb_program(config),
                        __env__.delayed_job_scheduler_program(config),
                        __env__.transactional_email_worker_program(config, 2)
                ),
                ssh_port=22
        ),
        'db': veil_server(
                host_name=host_name,
                sequence_no=30,
                mount_data_dir=True,
                programs=merge_multiple_settings(
                        __env__.persist_store_redis_program(config),
                        __env__.memory_cache_redis_program(config),
                        __env__.queue_program(config),
                        __env__.crowd_sorcery_postgresql_program(config, cw_postgresql_more_config),
                ),
                resources=[
                    ('veil.backend.database.client.database_client_resource', dict(purpose='crowd_sorcery', config=__env__.crowd_sorcery_config(config).crowd_sorcery_database_client))
                ],
                ssh_port=22
        )
    }, config


def crowd_sorcery_public_env(host_no):
    env_name = 'crowd_sorcery-public' if host_no == 2 else 'crowd_sorcery-public--{}'.format(host_no)
    host_name = 'crowd_sorceryhost-{:02d}'.format(host_no)
    mac_prefix = '00:16:3e:73:{:02d}'.format(host_no)
    lan_range = '10.27.{}'.format(host_no)
    web_ip = '{}.10'.format(lan_range)
    sorted_server_names, servers, config = crowd_sorcery_public_servers(
            host_name, lan_range,
            crowd_website_domain='www.tgcaem.org',
            operator_website_domain='op.tgcaem.org',
    )

    host_iptables_rules = [
        iptables_rule_resource(table='nat', rule='PREROUTING -i {} -p tcp -m tcp --dport 80 -j DNAT --to-destination {}:80'.format(EXTERNAL_NIC, web_ip)),
        iptables_rule_resource(table='nat',
                               rule='PREROUTING -i {0} -p tcp -m tcp --dport {1} -j DNAT --to-destination {2}:{1}'.format(EXTERNAL_NIC, 443, web_ip))
    ]
    hosts = {
        host_name: veil_host(
                lan_range,
                'lan',
                mac_prefix,
                '{}.tgcaem.org'.format(host_name),
                sshd_config=('PasswordAuthentication no', 'GatewayPorts clientspecified', 'MaxSessions 128'),
                iptables_rule_resources=host_iptables_rules
        )
    }
    env = {
        env_name: veil_env(
                name=env_name,
                hosts=hosts,
                servers=servers,
                sorted_server_names=sorted_server_names,
                deployment_memo='',
                config=config
        )
    }

    return env


ENV_PUBLIC = dict(crowd_sorcery_public_env(2), **crowd_sorcery_public_env(3))
