from django.contrib import admin
from .models import Category, Article, BlogComment, Comment, UserProfile, Tag, MediaFile, Blog
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name',]

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name',]

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'author','view_counts', 'created_at', 'updated_at']
    list_filter = ['status', 'author', 'category', 'created_at']
    search_fields = ['title', 'content', ]
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_counts']
    date_hierarchy = 'created_at'

    fieldsets = (
    ('Content', {
        'fields': ('title', 'slug', 'content', 'summary')
    }),
    ('Organization', {
        'fields': ('author', 'category', 'tags', 'status')
    }),
    ('Media', {
        'fields': ('featured_image',)
    }),
    ('Analytics', {
        'fields': ('view_counts', 'published_at')
    }),
    ('Metadata', {
        'fields': ('meta_title', 'meta_description')
    }),
)
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status', 'author', 'category', 
        'view_count', 'like_count', 'is_featured', 
        'published_date', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'is_featured', 'is_sticky',
        'allow_comments', 'published_date', 'created_at'
    ]
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'like_count', 'share_count', 'reading_time']
    date_hierarchy = 'published_date'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        ('Organization', {
            'fields': ('author', 'category', 'tags', 'status')
        }),
        ('Media', {
            'fields': ('featured_image', 'banner_image')
        }),
        ('Analytics', {
            'fields': ('view_count', 'like_count', 'share_count', 'reading_time')
        }),
        ('Settings', {
            'fields': ('allow_comments', 'is_featured', 'is_sticky', 'is_original')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Publication', {
            'fields': ('published_date', 'source_url')
        }),
    )

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = [
        'content_preview', 'blog', 'author', 'author_name', 
        'status', 'is_approved', 'created_at'
    ]
    list_filter = ['status', 'is_approved', 'created_at']
    search_fields = ['content', 'author_name', 'author_email']
    actions = ['approve_comments', 'mark_as_spam']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'
    
    def approve_comments(self, request, queryset):
        queryset.update(status='APPROVED', is_approved=True)
    approve_comments.short_description = 'Approve selected comments'
    
    def mark_as_spam(self, request, queryset):
        queryset.update(status='SPAM', is_approved=False)
    mark_as_spam.short_description = 'Mark selected as spam'
@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'is_public', 'created_at']
    search_fields = ['file_name', 'alt_text', 'caption']
    readonly_fields = ['file_size', 'created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'article', 'author', 'status', 'created_at']
    list_filter = ['status', 'is_approved', 'created_at']
    search_fields = ['content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'bio']

