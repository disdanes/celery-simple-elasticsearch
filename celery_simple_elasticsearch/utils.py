from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from django.db import connection

from .conf import settings


def get_update_task(task_path=None):
    default_task = settings.CELERY_SIMPLE_ELASTICSEARCH_DEFAULT_TASK
    import_path = task_path or default_task

    module, attr = import_path.rsplit('.', 1)
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' %
                                   (module, e))
    try:
        Task = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '
                                   'class.' % (module, attr))
    return Task()


def enqueue_task(action, instance):
    """
    Common utility for enqueing a task for the given action and
    model instance.
    """
    identifier = instance.get_identifier(instance)
    kwargs = {}
    if settings.CELERY_SIMPLE_ELASTICSEARCH_QUEUE:
        kwargs['queue'] = settings.CELERY_SIMPLE_ELASTICSEARCH_QUEUE
    if settings.CELERY_SIMPLE_ELASTICSEARCH_COUNTDOWN:
        kwargs['countdown'] = settings.CELERY_SIMPLE_ELASTICSEARCH_COUNTDOWN
    task = get_update_task()
    if hasattr(connection, 'on_commit'):
        connection.on_commit(
            lambda: task.apply_async((action, identifier), {}, **kwargs)
        )
    else:
        task.apply_async((action, identifier), {}, **kwargs)
