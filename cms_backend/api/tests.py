from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import permissions
from api.models import Article, Blog, Category, Tag
from api.serializers import (
    ArticleSerializer, ArticleListSerializer, ArticleDetailSerializer,
    BlogListSerializer, BlogDetailSerializer
)
from api.views import (
    ArticleDetailView, ArticleStatsView, BlogFeaturedView,
    DashboardStatsView, GlobalSearchView
)

class BackendFixesTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.admin = User.objects.create_superuser(username="adminuser", password="password")
        self.category = Category.objects.create(name="Tech", slug="tech")
        self.tag = Tag.objects.create(name="django", slug="django")
        
        # Create an Article
        self.article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            content="This is the content.",
            summary="Summary.",
            author=self.user,
            category=self.category,
            status="PUBLISHED",
            published_at=timezone.now()
        )
        self.article.tags.add(self.tag)

        # Create a Blog
        self.blog = Blog.objects.create(
            title="Test Blog",
            slug="test-blog",
            content="Blog content.",
            excerpt="Excerpt.",
            author=self.user,
            category=self.category,
            status="PUBLISHED",
            published_date=timezone.now(),
            is_featured=True
        )
        self.blog.tags.add(self.tag)

    def test_serializers_instantiation(self):
        """Verify that all main serializers instantiate and validate fields without errors"""
        
        # Test ArticleSerializer
        article_serializer = ArticleSerializer(instance=self.article)
        self.assertIn("view_counts", article_serializer.data)
        self.assertIn("published_at", article_serializer.data)
        self.assertNotIn("view_count", article_serializer.data)
        self.assertNotIn("publish_date", article_serializer.data)

        # Test ArticleListSerializer
        list_serializer = ArticleListSerializer(instance=self.article)
        self.assertIn("view_counts", list_serializer.data)
        self.assertIn("published_at", list_serializer.data)

        # Test ArticleDetailSerializer
        detail_serializer = ArticleDetailSerializer(instance=self.article)
        self.assertIn("view_counts", detail_serializer.data)
        self.assertIn("published_at", detail_serializer.data)
        
        # Test next/previous article logic
        # Create another article
        next_article = Article.objects.create(
            title="Next Article",
            slug="next-article",
            content="More content.",
            author=self.user,
            status="PUBLISHED",
            published_at=timezone.now() + timezone.timedelta(days=1)
        )
        detail_serializer_updated = ArticleDetailSerializer(instance=self.article)
        self.assertIsNotNone(detail_serializer_updated.data["next_article"])
        self.assertEqual(detail_serializer_updated.data["next_article"]["id"], next_article.id)

        # Test Blog serializers
        blog_list_serializer = BlogListSerializer(instance=self.blog)
        self.assertIn("published_date", blog_list_serializer.data)
        self.assertNotIn("publish_date", blog_list_serializer.data)

        blog_detail_serializer = BlogDetailSerializer(instance=self.blog)
        self.assertIn("published_date", blog_detail_serializer.data)
        self.assertNotIn("publish_date", blog_detail_serializer.data)

    def test_view_permissions_are_instances(self):
        """Verify that get_permissions returns instantiated permission class instances, not class objects"""
        view = ArticleDetailView()
        
        # Test GET request permissions
        factory = APIRequestFactory()
        view.request = factory.get(reverse('api:article-detail', kwargs={'pk': self.article.pk}))
        permissions_list = view.get_permissions()
        self.assertEqual(len(permissions_list), 1)
        self.assertIsInstance(permissions_list[0], permissions.AllowAny)

        # Test PUT request permissions
        view.request = factory.put(reverse('api:article-detail', kwargs={'pk': self.article.pk}))
        permissions_list = view.get_permissions()
        self.assertEqual(len(permissions_list), 1)
        self.assertIsInstance(permissions_list[0], permissions.IsAuthenticated)

    def test_article_stats_view_query(self):
        """Verify that ArticleStatsView correctly executes the query using view_counts instead of view_count"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('api:article-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_views"], 0)

    def test_blog_featured_view_query(self):
        """Verify that BlogFeaturedView correctly executes query using published_date instead of publish_date"""
        response = self.client.get(reverse('api:blog-featured'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Test Blog")

    def test_dashboard_stats_view_query(self):
        """Verify that DashboardStatsView correctly executes dashboard query without FieldError"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('api:dashboard-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_articles"], 1)
        self.assertEqual(response.data["total_blogs"], 1)

    def test_global_search_view_compiles_and_runs(self):
        """Verify that GlobalSearchView with self parameter runs and returns results"""
        response = self.client.get(f"{reverse('api:global-search')}?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["articles"]), 1)
        self.assertEqual(len(response.data["blogs"]), 1)
