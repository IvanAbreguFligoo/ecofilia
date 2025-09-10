from .base import *

ENVIRONMENT_NAME = "Production"

# ALLOWED_HOSTS += ["*"]
STATIC_ROOT = BASE_DIR + "/django-static/"
STATIC_URL = "/django-static/"

import os

# Celery broker: AWS SQS
CELERY_BROKER_URL = "sqs://"

# No result backend (fire-and-forget)
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_STORE_EAGER_RESULT = False

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
SQS_REGION = os.environ.get("SQS_REGION", "us-east-2")

if not SQS_QUEUE_URL:
    raise RuntimeError("SQS_QUEUE_URL environment variable is not set")

CELERY_BROKER_TRANSPORT_OPTIONS = {
    "region": SQS_REGION,
    "wait_time_seconds": 20,      # long polling
    "visibility_timeout": 3600,   # >= max task runtime
    "predefined_queues": {
        "celery": {  # name must match CELERY_TASK_DEFAULT_QUEUE
            "url": SQS_QUEUE_URL
        }
    },
    "queue_name_prefix": ""       # keep names exact
}

# Default queue name
CELERY_TASK_DEFAULT_QUEUE = "celery"

# Reliability settings for SQS
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"

# Timezone
CELERY_ENABLE_UTC = True
TIME_ZONE = "UTC"


INSTALLED_APPS += ["storages"]

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "virtual"
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_S3_FILE_OVERWRITE = False

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},  # MEDIA
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"