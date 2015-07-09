from django.db.models import signals

from .utils import enqueue_task
from .indexes import CelerySearchIndex


class CelerySignalProcessor(object):

    def setup(self):
        signals.post_save.connect(self.enqueue_save)
        signals.post_delete.connect(self.enqueue_delete)

    def teardown(self):
        signals.post_save.disconnect(self.enqueue_save)
        signals.post_delete.disconnect(self.enqueue_delete)

    def enqueue_save(self, sender, instance, **kwargs):
        return self.enqueue('update', instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)

    def enqueue(self, action, instance, sender, **kwargs):
        """
        Given an individual model instance, determine if a backend
        handles the model, check if the index is Celery-enabled and
        enqueue task.
        """

        if isinstance(instance, CelerySearchIndex):
            if action == 'update' and not instance.should_index(instance):
                continue
            enqueue_task(action, instance)
