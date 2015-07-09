from django.db.models import signals

from .utils import enqueue_task


class CelerySearchIndex(object):
    """
    Enqueues updates/deletes for later processing using Celery.
    """

    @classmethod
    def reindex_on_signals(cls, model=None, method=None):
        sender = model or cls

        cls._setup_save(sender, method)
        cls._setup_delete(sender, method)

    @classmethod
    def _setup_save(cls, model, method=None):
        if not method:
            method = cls.enqueue_save

        signals.post_save.connect(
            method,
            sender=model,
            dispatch_uid=CelerySearchIndex
        )

    @classmethod
    def _setup_delete(cls, model, method=None):
        if not method:
            method = cls.enqueue_delete

        signals.post_delete.connect(
            method,
            sender=model,
            dispatch_uid=CelerySearchIndex
        )

    @classmethod
    def _teardown_save(cls, model, method=None):
        if not method:
            method = cls.enqueue_save

        signals.post_save.disconnect(
            method,
            sender=model,
            dispatch_uid=CelerySearchIndex
        )

    @classmethod
    def _teardown_delete(cls, model, method=None):
        if not method:
            method = cls.enqueue_delete

        signals.post_delete.disconnect(
            method,
            sender=model,
            dispatch_uid=CelerySearchIndex
        )

    @classmethod
    def enqueue_save(cls, instance, **kwargs):
        if cls.should_index(instance):
            return cls.enqueue('update', instance)

    @classmethod
    def enqueue_delete(cls, instance, **kwargs):
        if cls.should_index(instance):
            return cls.enqueue('delete', instance)

    @classmethod
    def enqueue(cls, action, instance):
        """
        Shoves a message about how to update the index into the queue.

        This is a standardized string, resembling something like::

            ``notes.note.23``
            # ...or...
            ``weblog.entry.8``
        """
        return enqueue_task(action, instance)
