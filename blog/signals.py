# blog/signals.py

from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Post


@receiver(post_delete, sender=Post)
def delete_post_image(sender, instance, **kwargs):
    for field_name in ("cover_image", "image_2", "image_3"):
        image = getattr(instance, field_name)
        if image:
            image.delete(save=False)