from django.db import models
from django.utils.text import slugify
from PIL import Image
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
        
class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published')
    ]
    author = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="posts"
        )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='published'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    cover_image = models.ImageField(upload_to="post_covers/", blank=True, null=True)
    image_2 = models.ImageField(upload_to="post_covers/", blank=True, null=True)
    image_3 = models.ImageField(upload_to="post_covers/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            existing_posts = Post.objects.all()
            if self.pk is not None:
                existing_posts = existing_posts.exclude(pk=self.pk)

            while existing_posts.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
        for field_name in ("cover_image", "image_2", "image_3"):
            image = getattr(self, field_name)
            if image:
                img_path = image.path
                with Image.open(img_path) as img:
                    if img.height > 800 or img.width > 800:
                        img.thumbnail((800, 800))
                        img.save(img_path)
    
    def __str__(self):
        return self.title