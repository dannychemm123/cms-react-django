from django.urls import path
from . import views

# This namespace helps you reverse look up URLs later
app_name = 'api'

urlpatterns = [
   
    path('users/register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('users/profile/',views.UserProfileView.as_view(),name='user-profile'),
    path('users/',views.UserListview.as_view(),name = 'user-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag-detail'),
    
   
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('articles/stats/', views.ArticleStatsView.as_view(), name='article-stats'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    path('articles/<int:pk>/publish/', views.ArticlePublishView.as_view(), name='article-publish'),
    #path('articles/<int:pk>/archive/', views.ArticleArchiveView.as_view(), name='article-archive'),
   
    path('articles/<int:article_pk>/comments/', views.CommentListView.as_view(), name='article-comments'),
    
    
    path('blogs/', views.BlogListView.as_view(), name='blog-list'),
    path('blogs/featured/', views.BlogFeaturedView.as_view(), name='blog-featured'),
    path('blogs/<int:pk>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('blogs/<int:pk>/publish/', views.BlogPublishView.as_view(), name='blog-publish'),
    path('blogs/<int:pk>/like/', views.BlogLikeView.as_view(), name='blog-like'),
    path('blogs/<int:pk>/share/', views.BlogShareView.as_view(), name='blog-share'),
    
    # Blog Comments
    path('blogs/<int:blog_pk>/comments/', views.BlogCommentListView.as_view(), name='blog-comments'),
    
   
    path('media/', views.MediaFileListView.as_view(), name='media-list'),
    path('media/<int:pk>/', views.MediaFileDetailView.as_view(), name='media-detail'),
    
    
    path('comments/<int:pk>/approve/', views.CommentApproveView.as_view(), name='comment-approve'),
    
   
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    
   
    path('search/', views.GlobalSearchView.as_view(), name='global-search'),
    
    # ============================================
    # OPTIONAL: Include router URLs if using ViewSets
    # ============================================
    # path('', include(router.urls)),
    
]