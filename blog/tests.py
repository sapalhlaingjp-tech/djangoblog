from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import Category, Post


class PostSlugTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_duplicate_titles_get_unique_numbered_slugs(self):
        first_post = Post.objects.create(
            author=self.author,
            title="Hello World",
            content="First post",
        )
        second_post = Post.objects.create(
            author=self.author,
            title="Hello World",
            content="Second post",
        )
        third_post = Post.objects.create(
            author=self.author,
            title="Hello World",
            content="Third post",
        )

        self.assertEqual(first_post.slug, "hello-world")
        self.assertEqual(second_post.slug, "hello-world-1")
        self.assertEqual(third_post.slug, "hello-world-2")


class PostCoverImageSignalTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_deleting_post_deletes_its_cover_image(self):
        image_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(image_bytes, format="PNG")

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                post = Post.objects.create(
                    author=self.author,
                    title="Post with cover",
                    content="Post content",
                    cover_image=SimpleUploadedFile(
                        "cover.png",
                        image_bytes.getvalue(),
                        content_type="image/png",
                    ),
                )
                self.assertTrue(post.cover_image.storage.exists(post.cover_image.name))

                post.delete()

                self.assertFalse(post.cover_image.storage.exists(post.cover_image.name))


class PostListCategoryPaginationTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")
        self.category = Category.objects.create(name="Django")
        for index in range(7):
            Post.objects.create(
                author=self.author,
                title=f"Django post {index}",
                content="Post content",
                category=self.category,
            )
        Post.objects.create(
            author=self.author,
            title="Other category post",
            content="Post content",
        )

    def test_category_filter_is_preserved_across_pages(self):
        response = self.client.get("/", {"category": self.category.name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 6)
        self.assertContains(
            response,
            f'href="?page=2&amp;category={self.category.name}"',
        )
        self.assertNotContains(response, "Other category post")

        response = self.client.get(
            "/",
            {"page": 2, "category": self.category.name.lower()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertContains(response, "Django post 0")
        self.assertContains(
            response,
            f'href="?page=1&amp;category={self.category.name.lower()}"',
        )
        self.assertNotContains(response, "Other category post")
