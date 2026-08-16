from django.shortcuts import render

from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Article, Blog, Category, Tag, 
    MediaFile, Comment, BlogComment, UserProfile
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    CategorySerializer, TagSerializer,
    ArticleListSerializer, ArticleDetailSerializer, ArticleCreateUpdateSerializer,
    BlogListSerializer, BlogDetailSerializer, BlogCreateUpdateSerializer,
    MediaFileSerializer, MediaFileUploadSerializer,
    CommentSerializer, CommentCreateSerializer,
    BlogCommentSerializer,
    DashboardStatsSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for larger page sizes"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

class UserRegistrationView(generics.CreateAPIView):
    '''View for user registration'''
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        UserProfile.objects.create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

class UserListview(generics.ListAPIView):
    '''List all users (admin only)'''
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes= [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination

class CategoryListView(generics.ListCreateAPIView):
    '''Get List of all categories or creat new category'''
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Get update or delete a category'''
    queryset = Category.objects.all()
    serializer_class =  CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
class TagListView(generics.ListCreateAPIView):
    """List all tags or create new tag"""
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update or delete a tag"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class ArticleListView(generics.ListAPIView):
    '''List of all article or create new article'''
    queryset = Article.objects.all().order_by('-created_at')
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if  self.request.method =='POST':
            return ArticleCreateUpdateSerializer
        return ArticleListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Article.objects.all()
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(summary__icontains=search)
            )
        
        # Only show published articles to non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='PUBLISHED')
        elif self.request.query_params.get('published_only') == 'true':
            queryset = queryset.filter(status='PUBLISHED')
        
        return queryset
    def perform_create(self,serializer):
        serializer.save(author = self.request.user)

class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Get, update or delete an article'''
    queryset = Article.objects.all()
    def get_serializer_class(self):
        if self.request.method in ['PUT','PATCH']:
            return ArticleCreateUpdateSerializer
        return ArticleDetailSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def retrieve(self,*args, **kwargs):
        instance = self.get_object()

        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ArticlePublishView(APIView):
    '''Publish Article'''
    permission_classes = [permissions.IsAuthenticated]

    def post(self,request,pk):
        article = get_object_or_404(Article,pk=pk)
        article.status = 'PUBLISHED'
        article.published_at = timezone.now()
        article.save()

        serializer = ArticleDetailSerializer(article)
        return Response(
            {
            'message': 'Article published successfully',
            'article': serializer.data
            }
        )

class ArticleStatsView(APIView):
    """Get article statistics"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_articles': Article.objects.count(),
            'published_articles': Article.objects.filter(status='PUBLISHED').count(),
            'draft_articles': Article.objects.filter(status='DRAFT').count(),
            'archived_articles': Article.objects.filter(status='ARCHIVED').count(),
            'total_views': Article.objects.aggregate(total=Sum('view_counts'))['total'] or 0,
        }
        return Response(stats)


class BlogListView(generics.ListCreateAPIView):
    """List all blogs or create new blog"""
    queryset = Blog.objects.all().order_by('-created_at')
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BlogCreateUpdateSerializer
        return BlogListSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        queryset = Blog.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(excerpt__icontains=search)
            )
        
        # Featured only
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Only show published blogs to non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='PUBLISHED')
        elif self.request.query_params.get('published_only') == 'true':
            queryset = queryset.filter(status='PUBLISHED')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class BlogDetailView(generics.RetrieveUpdateDestroyAPIView):
    '''Get, update and delete a blog'''
    queryset = Blog.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BlogCreateUpdateSerializer
        return BlogDetailSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_view_count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class BlogPublishView(APIView):
    permission_classes =[permissions.IsAuthenticated]

    def post(self,request,pk):
        blog = get_object_or_404(Blog,pk=pk)
        blog.status = 'PUBLISHED'
        blog.published_date = timezone.now()
        blog.save()
        serializer = BlogDetailSerializer(blog)
        return Response({
            'message': 'Blog published successfully',
            'blog': serializer.data
        })    


class BlogLikeView(APIView):
    """Like or unlike a blog"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        blog.increment_like_count()
        
        return Response({
            'message': 'Blog liked',
            'like_count': blog.like_count
        })

class BlogShareView(APIView):
    """Track blog share"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        blog.increment_share_count()
        
        return Response({
            'message': 'Share tracked',
            'share_count': blog.share_count
        })

class BlogFeaturedView(APIView):
    """Get featured blogs"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        blogs = Blog.objects.filter(
            status='PUBLISHED',
            is_featured=True
        ).order_by('-published_date')[:6]
        
        serializer = BlogListSerializer(blogs, many=True)
        return Response(serializer.data)

class MediaFileListView(generics.ListCreateAPIView):
    """List all media files or upload new file"""
    queryset = MediaFile.objects.all().order_by('-created_at')
    serializer_class = MediaFileSerializer
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        queryset = MediaFile.objects.all()
        
        # Filter by file type
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type.upper())
        
        # Filter by public/private
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(file_name__icontains=search) |
                Q(alt_text__icontains=search) |
                Q(caption__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        # Validate upload
        upload_serializer = MediaFileUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        
        # Create media file
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        media_file = MediaFile(
            file=file_obj,
            file_name=file_obj.name,
            mime_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=request.user,
            alt_text=upload_serializer.validated_data.get('alt_text', ''),
            caption=upload_serializer.validated_data.get('caption', ''),
            description=upload_serializer.validated_data.get('description', ''),
            is_public=upload_serializer.validated_data.get('is_public', True),
        )
        
        # Check if linked to article
        article_id = upload_serializer.validated_data.get('article_id')
        if article_id:
            try:
                article = Article.objects.get(id=article_id)
                media_file.article = article
            except Article.DoesNotExist:
                pass
        
        media_file.save()
        
        serializer = MediaFileSerializer(media_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MediaFileDetailView(generics.RetrieveDestroyAPIView):
    """Get or delete a media file"""
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = MediaFile.objects.all()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset



class CommentListView(generics.ListCreateAPIView):
    """List comments for an article or create new comment"""
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        article_id = self.kwargs.get('article_pk')
        if article_id:
            return Comment.objects.filter(
                article_id=article_id,
                is_approved=True,
                parent__isnull=True
            ).order_by('created_at')
        return Comment.objects.none()
    
    def perform_create(self, serializer):
        article_id = self.kwargs.get('article_pk')
        article = get_object_or_404(Article, pk=article_id)
        
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user, article=article)
        else:
            serializer.save(article=article)


class BlogCommentListView(generics.ListCreateAPIView):
    """List comments for a blog or create new comment"""
    serializer_class = BlogCommentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        blog_id = self.kwargs.get('blog_pk')
        if blog_id:
            return BlogComment.objects.filter(
                blog_id=blog_id,
                is_approved=True,
                parent__isnull=True
            ).order_by('created_at')
        return BlogComment.objects.none()
    
    def perform_create(self, serializer):
        blog_id = self.kwargs.get('blog_pk')
        blog = get_object_or_404(Blog, pk=blog_id)
        
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user, blog=blog)
        else:
            serializer.save(blog=blog)


class CommentApproveView(APIView):
    """Approve a comment"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        comment.approve()
        return Response({'message': 'Comment approved'})



class DashboardStatsView(APIView):
    """Get dashboard statistics"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_articles': Article.objects.count(),
            'published_articles': Article.objects.filter(status='PUBLISHED').count(),
            'draft_articles': Article.objects.filter(status='DRAFT').count(),
            'total_blogs': Blog.objects.count(),
            'published_blogs': Blog.objects.filter(status='PUBLISHED').count(),
            'total_media': MediaFile.objects.count(),
            'total_users': User.objects.count(),
            'total_comments': Comment.objects.count(),
            'pending_comments': Comment.objects.filter(status='PENDING').count(),
            'recent_articles': ArticleListSerializer(
                Article.objects.filter(status='PUBLISHED').order_by('-published_at')[:5],
                many=True
            ).data,
            'recent_blogs': BlogListSerializer(
                Blog.objects.filter(status='PUBLISHED').order_by('-published_date')[:5],
                many=True
            ).data,
        }
        
        serializer = DashboardStatsSerializer(data=stats)
        serializer.is_valid()
        return Response(serializer.data)

    

class GlobalSearchView(APIView):
    '''Global search acrosss article and Blog'''
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q','')
        if not query:
            return Response({
                'articles': [],
                'blogs': [],
                'categories': [],
                'tags': []
            })
        articles = Article.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(summary__icontains=query),
            status='PUBLISHED'
        )[:10]
        
        # Search blogs
        blogs = Blog.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query),
            status='PUBLISHED'
        )[:10]
        
        # Search categories
        categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        
        # Search tags
        tags = Tag.objects.filter(name__icontains=query)[:5]
        
        return Response({
            'articles': ArticleListSerializer(articles, many=True).data,
            'blogs': BlogListSerializer(blogs, many=True).data,
            'categories': CategorySerializer(categories, many=True).data,
            'tags': TagSerializer(tags, many=True).data,
        })