from django.urls import path
from .views import PostListView, PostDetailView,PostUpdateView, PostDeleteView, about, contact, PostCreateView, RegisterView,MyPostsView

urlpatterns = [
    path("", PostListView.as_view(), name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("my-posts/", MyPostsView.as_view(), name="my_posts"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("posts/<slug:slug>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
]
