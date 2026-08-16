from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
# pyrefly: ignore [missing-import]
from .models import (
    Category, Article, BlogComment, Comment, UserProfile, Tag, MediaFile, Blog


)
class UserSerializer(serializers.ModelSerializer):
    '''Serializer for the User model.'''
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'is_active']
        read_only_fields = ['id', 'is_active']

    def get_full_name(self,obj):
        '''Get the full name of the user.'''
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer with nested user"""
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'bio', 'profile_picture', 
                 'website', 'location', 'social_links', 'email_notifications', 
                 'theme_preference', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, data):
        """Validate that the two passwords match."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """Create a new user and associated profile."""
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)  # Create an associated UserProfile
        return user

class CategorySerializer(serializers.ModelSerializer):
    '''Serializer for the Category model.'''
    article_count = serializers.IntegerField(source='articles.count', read_only=True)
    blog_count = serializers.IntegerField(source='blogs.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 
                 'article_count', 'blog_count']
        read_only_fields = ['id', 'created_at']

    def get_article_count(self, obj):
        return obj.articles.filter(status='PUBLISHED').count()
    
    def get_blog_count(self, obj):
        return obj.blogs.filter(status='PUBLISHED').count()

class TagSerializer(serializers.ModelSerializer):
    '''Serializer for the Tag model.'''
    article_count = serializers.IntegerField(source='articles.count', read_only=True)
    blog_count = serializers.IntegerField(source='blogs.count', read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at', 
                  'article_count', 'blog_count']
        read_only_fields = ['id', 'created_at']

    def get_article_count(self, obj):
        return obj.articles.filter(status='PUBLISHED').count()
    
    def get_blog_count(self, obj):
        return obj.blogs.filter(status='PUBLISHED').count()

class ArticleSerializer(serializers.ModelSerializer):
    '''serializer for the Article model.'''
    author_name = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True,allow_null=True)
    tags_list = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'summary', 'status', 'category', 'category_name',
            'author', 'author_name', 'tags_list', 'featured_image', 
            'view_counts', 'published_at', 'created_at', 'comment_count'
        ]
        read_only_fields = ['id','view_counts','created_at']
    def get_tags_list(self,obj):
        '''Get a list of tag names associated with the article.'''
        return [tag.name for tag in obj.tags.all()]

    def get_comment_count(self,obj):
        '''Get the count of comments associated with the article.'''
        return obj.comments.filter(is_approved=True).count()

class ArticleListSerializer(serializers.ModelSerializer):
    """Article serializer for list views (lightweight)"""
    author_name = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    tags_list = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    featured_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 
            'title', 
            'slug', 
            'summary', 
            'status', 
            'category', 
            'category_name',
            'author', 
            'author_name', 
            'tags_list', 
            'featured_image',
            'featured_image_url',
            'view_counts', 
            'published_at', 
            'created_at', 
            'updated_at',
            'comment_count'
        ]
        read_only_fields = ['id', 'view_counts', 'created_at', 'updated_at']
    
    def get_tags_list(self, obj):
        return [tag.name for tag in obj.tags.all()]
    
    def get_comment_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
    def get_featured_image_url(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None


class ArticleDetailSerializer(serializers.ModelSerializer):
    '''Detail serializer for the Article model. for full view of the article.'''
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    next_article = serializers.SerializerMethodField()
    previous_article = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [

            'id', 'title', 'slug', 'content', 'summary', 'status',
            'author', 'category', 'tags', 'featured_image',
            'view_counts', 'published_at', 'created_at', 'updated_at',
            'meta_title', 'meta_description', 'comments',
            'next_article', 'previous_article'
        ]
        read_only_fields = ['id', 'view_counts', 'created_at', 'updated_at']

    def get_comments(self,obj):
        '''Get approved comment of the article.'''
        approved_comments = obj.comments.filter(is_approved=True)
        return CommentSerializer(approved_comments, many=True).data

    def get_next_article(self,obj):
        '''Get the next article base on the publish date.'''
        if not obj.published_at:
            return None
        next_article = Article.objects.filter(published_at__gt=obj.published_at, status='PUBLISHED').order_by('published_at').first()
        if next_article:
            return {'id':next_article.id, 'title': next_article.title, 'slug': next_article.slug}
        return None

    def get_previous_article(self,obj):
        '''Get previous published article'''
        if not obj.published_at:
            return None
        prev_article = Article.objects.filter(
            status='PUBLISHED', published_at__lt=obj.published_at).order_by('-published_at').first()
        if prev_article:
            return {'id': prev_article.id, 'title': prev_article.title, 'slug': prev_article.slug}
        return None

    
class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """Article serializer for create/update operations"""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'summary', 'status',
            'category', 'tags', 'featured_image',
            'meta_title', 'meta_description'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create article with tags"""
        tags_data = validated_data.pop('tags', [])
        article = Article.objects.create(**validated_data)
        
        # Handle tags
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
            article.tags.add(tag)
        
        return article
    
    def update(self, instance, validated_data):
        """Update article with tags"""
        tags_data = validated_data.pop('tags', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags
        if tags_data is not None:
            instance.tags.clear()
            for tag_name in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                instance.tags.add(tag)
        
        return instance

class BlogListSerializer(serializers.ModelSerializer):
    """Blog serializer for list views (lightweight)"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    tags_list = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'excerpt', 'status', 'category', 'category_name',
            'author', 'author_name', 'tags_list', 'featured_image',
            'view_count', 'like_count', 'reading_time', 'is_featured', 'is_sticky',
            'published_date', 'created_at', 'comment_count'
        ]
        read_only_fields = ['id', 'view_count', 'like_count', 'share_count', 'created_at']
    
    def get_tags_list(self, obj):
        return [tag.name for tag in obj.tags.all()]
    
    def get_comment_count(self, obj):
        return obj.blog_comments.filter(is_approved=True).count()


class BlogDetailSerializer(serializers.ModelSerializer):
    """Blog serializer for detail views (full data)"""
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    related_blogs = serializers.SerializerMethodField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'status',
            'author', 'category', 'tags', 'featured_image', 'banner_image',
            'view_count', 'like_count', 'share_count', 'reading_time',
            'allow_comments', 'is_featured', 'is_sticky', 'is_original',
            'published_date', 'created_at', 'updated_at',
            'meta_title', 'meta_description', 'meta_keywords',
            'source_url', 'comments', 'related_blogs'
        ]
        read_only_fields = [
            'id', 'view_count', 'like_count', 'share_count', 
            'created_at', 'updated_at'
        ]
    
    def get_comments(self, obj):
        approved_comments = obj.blog_comments.filter(is_approved=True)
        return BlogCommentSerializer(approved_comments, many=True).data
    
    def get_related_blogs(self, obj):
        """Get related blogs"""
        related = obj.get_related_blogs(limit=5)
        return BlogListSerializer(related, many=True).data


class BlogCreateUpdateSerializer(serializers.ModelSerializer):
    """Blog serializer for create/update operations"""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'status',
            'category', 'tags', 'featured_image', 'banner_image',
            'allow_comments', 'is_featured', 'is_sticky', 'is_original',
            'meta_title', 'meta_description', 'meta_keywords',
            'source_url'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create blog with tags"""
        tags_data = validated_data.pop('tags', [])
        blog = Blog.objects.create(**validated_data)
        
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
            blog.tags.add(tag)
        
        return blog
    
    def update(self, instance, validated_data):
        """Update blog with tags"""
        tags_data = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags_data is not None:
            instance.tags.clear()
            for tag_name in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                instance.tags.add(tag)
        
        return instance

class MediaFileSerializer(serializers.ModelSerializer):
    """Media file serializer"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'file', 'file_name', 'file_type', 'mime_type', 
            'file_size', 'file_size_mb', 'file_url', 'thumbnail_url',
            'alt_text', 'caption', 'description', 'dimensions',
            'uploaded_by', 'uploaded_by_name', 'article',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'created_at', 'updated_at']
    
    def get_file_size_mb(self, obj):
        return obj.get_file_size_mb()
    
    def get_file_url(self, obj):
        return obj.get_file_url()
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class MediaFileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads"""
    file = serializers.FileField(required=True)
    alt_text = serializers.CharField(max_length=255, required=False, allow_blank=True)
    caption = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    article_id = serializers.IntegerField(required=False, allow_null=True)
    is_public = serializers.BooleanField(default=True)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 50MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 
                        'video/mp4', 'video/webm', 'audio/mpeg', 'audio/wav',
                        'application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(f"File type {value.content_type} is not allowed")
        
        return value




class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer"""
    author_name_display = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'status', 'is_approved',
            'author', 'author_name', 'author_name_display', 'avatar_url',
            'author_email', 'parent', 'replies',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'status', 'is_approved', 'created_at']
    
    def get_author_name_display(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return obj.author_name or 'Anonymous'
    
    def get_avatar_url(self, obj):
        if obj.author:
            # Use gravatar with email
            import hashlib
            email_hash = hashlib.md5(obj.author.email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=40"
        elif obj.author_email:
            import hashlib
            email_hash = hashlib.md5(obj.author_email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=40"
        return None
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True)
        return CommentSerializer(replies, many=True).data
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%B %d, %Y at %I:%M %p")


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    class Meta:
        model = Comment
        fields = ['content', 'author_name', 'author_email', 'parent', 'article']
    
    def validate(self, data):
        """Validate comment data"""
        # If user is authenticated, ignore author_name and author_email
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            data['author'] = request.user
            data['author_name'] = None
            data['author_email'] = None
        
        # Check if article exists
        if 'article' in data:
            
            try:
                Article.objects.get(id=data['article'].id)
            except Article.DoesNotExist:
                raise serializers.ValidationError({"article": "Article not found"})
        
        return data


class BlogCommentSerializer(serializers.ModelSerializer):
    """Blog comment serializer"""
    author_name_display = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'content', 'status', 'is_approved',
            'author', 'author_name', 'author_name_display', 'avatar_url',
            'author_email', 'author_website', 'parent', 'replies',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'status', 'is_approved', 'created_at']
    
    def get_author_name_display(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return obj.author_name or 'Anonymous'
    
    def get_avatar_url(self, obj):
        if obj.author:
            import hashlib
            email_hash = hashlib.md5(obj.author.email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=40"
        elif obj.author_email:
            import hashlib
            email_hash = hashlib.md5(obj.author_email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=mp&s=40"
        return None
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True)
        return BlogCommentSerializer(replies, many=True).data
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%B %d, %Y at %I:%M %p")




class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_articles = serializers.IntegerField()
    published_articles = serializers.IntegerField()
    draft_articles = serializers.IntegerField()
    total_blogs = serializers.IntegerField()
    published_blogs = serializers.IntegerField()
    total_media = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    pending_comments = serializers.IntegerField()