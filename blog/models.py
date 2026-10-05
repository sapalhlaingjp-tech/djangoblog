from django.db import models
from django.utils.text import slugify

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
     if not self.slug:
        self.slug = slugify(self.title, allow_unicode=True)
     super().save(*args, **kwargs)    

    def __str__(self):
        return self.title