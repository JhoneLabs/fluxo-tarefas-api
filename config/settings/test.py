from .base import *

# Test settings
DEBUG = False

# Celery test configuration - tasks run synchronously and eagerly in test environment
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Fast password hasher for faster test execution
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
