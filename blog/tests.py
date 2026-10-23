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
                    image_2=SimpleUploadedFile(
                        "photo-2.png",
                        image_bytes.getvalue(),
                        content_type="image/png",
                    ),
                    image_3=SimpleUploadedFile(
                        "photo-3.png",
                        image_bytes.getvalue(),
                        content_type="image/png",
                    ),
                )
                image_files = tuple(
                    (image.storage, image.name)
                    for image in (post.cover_image, post.image_2, post.image_3)
                )
                self.assertTrue(
                    all(storage.exists(name) for storage, name in image_files)
                )

                post.delete()

                self.assertTrue(
                    all(not storage.exists(name) for storage, name in image_files)
                )


class PostFormImageTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username="author",
            password="password",
        )

    def make_image(self, name):
        image_bytes = BytesIO()
        Image.new("RGB", (10, 10)).save(image_bytes, format="PNG")
        return SimpleUploadedFile(
            name,
            image_bytes.getvalue(),
            content_type="image/png",
        )

    def test_post_creation_requires_three_images_and_shows_them(self):
        self.client.login(username="author", password="password")
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                data = {
                    "title": "Photo story",
                    "content": "A story with three photographs.",
                    "status": "published",
                    "cover_image": self.make_image("photo-1.png"),
                    "image_2": self.make_image("photo-2.png"),
                    "image_3": self.make_image("photo-3.png"),
                }

                response = self.client.post("/posts/new/", data)

                self.assertEqual(response.status_code, 302)
                post = Post.objects.get(title="Photo story")
                self.assertTrue(post.cover_image)
                self.assertTrue(post.image_2)
                self.assertTrue(post.image_3)

                response = self.client.get(f"/posts/{post.slug}/")

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'src="{post.cover_image.url}"')
                self.assertContains(response, f'src="{post.image_2.url}"')
                self.assertContains(response, f'src="{post.image_3.url}"')

    def test_post_creation_rejects_fewer_than_three_images(self):
        self.client.login(username="author", password="password")
        response = self.client.post(
            "/posts/new/",
            {
                "title": "Photo story",
                "content": "A story with missing photographs.",
                "status": "published",
                "cover_image": self.make_image("photo-1.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please upload all 3 post photos.")
        self.assertFalse(Post.objects.filter(title="Photo story").exists())

    def test_existing_post_can_be_saved_without_reuploading_its_photos(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                post = Post.objects.create(
                    author=self.author,
                    title="Existing photo story",
                    content="An existing story with three photographs.",
                    cover_image=self.make_image("photo-1.png"),
                    image_2=self.make_image("photo-2.png"),
                    image_3=self.make_image("photo-3.png"),
                )
                self.client.login(username="author", password="password")

                response = self.client.post(
                    f"/posts/{post.slug}/edit/",
                    {
                        "title": post.title,
                        "content": post.content,
                        "status": post.status,
                    },
                )

                self.assertEqual(response.status_code, 302)
                post.refresh_from_db()
                self.assertEqual(post.cover_image.name, "post_covers/photo-1.png")
                self.assertEqual(post.image_2.name, "post_covers/photo-2.png")
                self.assertEqual(post.image_3.name, "post_covers/photo-3.png")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
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
        self.assertContains(response, "Discover Myanmar Shan State")
        self.assertContains(response, "blog/videos/IMG_5356.MP4")
        self.assertContains(response, "Open sound")
        self.assertContains(response, "aria-pressed=\"false\"")
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


class AuthorPostsTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")
        self.visitor = get_user_model().objects.create_user(username="visitor")
        self.published_post = Post.objects.create(
            author=self.author,
            title="Published by author",
            content="Public content",
            status="published",
        )
        Post.objects.create(
            author=self.author,
            title="Draft by author",
            content="Private draft",
            status="draft",
        )
        Post.objects.create(
            author=self.visitor,
            title="Visitor's post",
            content="Other author's content",
            status="published",
        )

    def test_anonymous_visitors_can_view_an_authors_published_posts(self):
        response = self.client.get("/my-posts/author/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Posts by author")
        self.assertContains(response, "Published by author")
        self.assertNotContains(response, "Draft by author")
        self.assertNotContains(response, "Visitor's post")
        self.assertEqual(
            list(response.context["page_obj"].object_list),
            [self.published_post],
        )

    def test_unknown_author_returns_404(self):
        response = self.client.get("/my-posts/unknown/")

        self.assertEqual(response.status_code, 404)

    def test_author_url_without_trailing_slash_redirects(self):
        response = self.client.get("/my-posts/author")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/my-posts/author/")

    def test_post_cards_link_to_the_authors_posts(self):
        response = self.client.get("/")

        self.assertContains(response, 'href="/my-posts/author/"')
