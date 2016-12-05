from __future__ import unicode_literals, print_function, division
from veil.profile.setting import *
from __env_development__ import ENV_DEVELOPMENT
from __env_test__ import ENV_TEST
from __env_public__ import ENV_PUBLIC

CODEBASE = 'git@git.tgcaem.org:/opt/git/crowd_sorcery.git'

ENVIRONMENTS = merge_multiple_settings(ENV_DEVELOPMENT, ENV_TEST, ENV_PUBLIC)

ENABLED_SMS_PROVIDERS = ()