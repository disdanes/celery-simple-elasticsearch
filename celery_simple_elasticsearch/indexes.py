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
    def instantiate_deleted_instance(cls, model_class, pk):
        """
        This specialized instantiation method is used to handle
        instances where we're deleting an instance from the index,
        and the actual instance is already gone from the db
        """
        class deleted_instance(object):
            pass

        deleted = deleted_instance()
        deleted.pk = pk

        return deleted

    @classmethod
    def enqueue_save(cls, instance, **kwargs):
        if cls.should_index(instance):
            return cls.enqueue(cls.index_add, instance)

    @classmethod
    def enqueue_delete(cls, instance, **kwargs):
        if cls.should_index(instance):
            return cls.enqueue(
                cls.index_delete,
                instance,
                cls.instantiate_deleted_instance
            )

    @classmethod
    def enqueue_action(cls, action, instance, **kwargs):
        if cls.should_index(instance):
            return cls.enqueue(action, instance)

    @classmethod
    def enqueue(cls, action, instance, instantiator=None):
        """
        Shoves a message about how to update the index into the queue.

        This is a standardized string, resembling something like::

            ``notes.note.23``
            # ...or...
            ``weblog.entry.8``

        The instantiator is an optional method which will handle instance
        instantiation.
        """
        return enqueue_task(action, instance, instantiator)
