from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
import uuid
import os
import hashlib

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Tag(models.Model):
    name = models.CharField(max_length=60,unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Article(models.Model):
   STATUS_CHOICES = [
       ('DRAFT', 'Draft'),
       ('PUBLISHED', 'Published'),
       ('ARCHIVED', 'Archived'),
   ]
   title = models.CharField(max_length=200)
   slug = models.SlugField(max_length=200, unique=True,blank =True)
   content = models.TextField()
   summary = models.TextField(blank=True,null=True)

   author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='articles')
   category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
   tags = models.ManyToManyField(Tag, related_name='articles', blank=True)
   status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   published_at = models.DateTimeField(blank = True, null=True)

   view_counts = models.IntegerField(default=0)

   featured_image = models.ImageField(upload_to='articles_images/',blank=True,null=True)

   meta_title = models.CharField(max_length=200, blank =True, null=True) 
   meta_description = models.TextField(max_length=500, blank=True,null=True)

   def __str__(self):
       return self.title

   def save(self, *args, **kwargs):
       if not self.slug:
           self.slug = slugify(self.title)

       if Article.objects.filter(slug=self.slug).exists():
           self.slug=f'{self.slug}-{str(uuid.uuid4())[:8]}'

       if self.status=='PUBLISHED' and not self.published_at:
           self.published_at = timezone.now()

       super().save(*args, **kwargs)

   def get_absolute_url(self):
       return reverse("article-detail", kwargs={"slug": self.slug})
   
   def increment_view_count(self):
       self.view_counts +=1
       self.save(update_fields = ['view_counts'])

   class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]


class Blog(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('PRIVATE', 'Private'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True, null=True, help_text="Short summary of the blog post")
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blogs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='blogs')
    tags = models.ManyToManyField(Tag, blank=True, related_name='blogs')
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    # Media
    featured_image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='blogs/banners/', blank=True, null=True)
    
    # Settings
    allow_comments = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False)  # Stick to top of blog list
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(max_length=500, blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma separated keywords")
    
    # Additional
    reading_time = models.IntegerField(default=0, help_text="Estimated reading time in minutes")
    source_url = models.URLField(blank=True, null=True, help_text="Original source URL if reposted")
    is_original = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
            
            # Make unique if needed
            import uuid
            if Blog.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        
        # Auto-set published date when status changes to published
        if self.status == 'PUBLISHED' and not self.published_date:
            self.published_date = timezone.now()
        
        # Auto-calculate reading time (approx 200 words per minute)
        if self.content and not self.reading_time:
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog-detail', kwargs={'slug': self.slug})
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_like_count(self):
        self.like_count += 1
        self.save(update_fields=['like_count'])
    
    def increment_share_count(self):
        self.share_count += 1
        self.save(update_fields=['share_count'])
    
    def get_related_blogs(self, limit=5):
        """Get related blogs based on tags and category"""
        related = Blog.objects.filter(
            status='PUBLISHED'
        ).exclude(
            id=self.id
        )
        
        # Filter by same category
        if self.category:
            related = related.filter(category=self.category)
        
        # Filter by tags
        if self.tags.exists():
            tag_ids = self.tags.values_list('id', flat=True)
            related = related.filter(tags__id__in=tag_ids).distinct()
        
        return related[:limit]
    
    def get_comments_count(self):
        """Get count of approved comments"""
        return self.blog_comments.filter(is_approved=True).count()
    
    @property
    def is_published(self):
        """Check if blog is published"""
        return self.status == 'PUBLISHED'
    
    @property
    def get_featured_image_url(self):
        """Get URL of featured image"""
        if self.featured_image:
            return self.featured_image.url
        return None
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_date']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_featured', 'is_sticky']),
        ]
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'


class MediaFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('DOCUMENT', 'Document'),
        ('OTHER', 'Other'),
    ]
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20,choices=FILE_TYPE_CHOICES,default='OTHER')
    mime_type = models.CharField(max_length=100,blank=True,null=True)
    file_size = models.BigIntegerField(default=0)


    alt_text = models.CharField(max_length=255,blank= True, null=True)
    caption = models.CharField(max_length=255,blank=True,null=True)
    description= models.TextField(blank=True,null=True)
    dimensions = models.CharField(max_length=50,blank=True,null=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='media_files')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='media_files')

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Thumbnail
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    
    def __str__(self):
        return self.file_name or "Unnamed Media"

    def save(self,*args,**kwargs):
        if self.file and not self.file_name:
            self.file_name = os.path.basename(self.file.name)


        if self.mime_type:
            if self.mime_type.startswith('image/'):
                self.file_type = 'IMAGE'
            elif self.mime_type.startswith('video/'):
                self.file_type = 'VIDEO'
            elif self.mime_type.startswith('audio/'):
                self.file_type = 'AUDIO'
            elif self.mime_type.startswith('application/'):
                self.file_type = 'DOCUMENT'
            else:
                self.file_type = 'OTHER'
    
        super().save(*args, **kwargs)

    def get_file_size_mb(self):
        '''Retune file size in mb'''
        if self.file:
            return round(self.file_size/(1024*1024),2)
        return 0

    def get_file_url(self):
        '''Get url of the file'''
        if self.file:
            return self.file.url
        return None

    class Meta:
        ordering =['-created_at']


class Comment(models.Model):
    STATUS_CHOICES = [
        ('PENDING','Pending'),
        ('APPROVED','Approved'),    
        ('SPAM','Spam'),
        ('TRASH','Trash'),

    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    is_approved = models.BooleanField(default=False)

    author_name = models.CharField(max_length=100, blank=True, null=True)
    author_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.author_name or "Anonymous"} on {self.article.title}'

    def approve(self):
        self.is_approved = True
        self.status = 'APPROVED'
        self.save()


class BlogComment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('SPAM', 'Spam'),
        ('TRASH', 'Trash'),
    ]
    
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='blog_comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_approved = models.BooleanField(default=False)
    
    # Anonymous author info
    author_name = models.CharField(max_length=100, blank=True, null=True)
    author_email = models.EmailField(blank=True, null=True)
    author_website = models.URLField(blank=True, null=True)
    
    # Tracking
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        author = self.author or self.author_name or 'Anonymous'
        return f"Comment by {author} on {self.blog.title}"
    
    def approve(self):
        self.is_approved = True
        self.status = 'APPROVED'
        self.save()
    
    def get_avatar_url(self):
        """Get gravatar URL based on email"""
        if self.author_email:
            email_hash = hashlib.md5(self.author_email.lower().encode()).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=mp"
        return None
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'is_approved']),
            models.Index(fields=['created_at']),
        ]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True, null=True, help_text="JSON object containing social media links")

    email_notifications = models.BooleanField(default=True)
    theme_preference = models.CharField(max_length=20, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    class Meta:
        db_table = 'user_profiles'