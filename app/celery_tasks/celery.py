from celery import Celery


celery = Celery('tasks', broker=f'redis://127.0.0.1:6379', include=['app.celery_tasks.model_training'])
celery.conf.broker_url = f'redis://127.0.0.1:6379'
celery.conf.broker_connection_retry = True
celery.conf.broker_connection_max_retries = None
celery.conf.result_backend = f'redis://127.0.0.1:6379'
