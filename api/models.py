from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(
            email=email,
            name=name,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Custom User model based on Asana's User schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='user')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    # Photo fields (simplified - in real implementation would store URLs)
    photo_21x21 = models.URLField(blank=True, null=True)
    photo_27x27 = models.URLField(blank=True, null=True)
    photo_36x36 = models.URLField(blank=True, null=True)
    photo_60x60 = models.URLField(blank=True, null=True)
    photo_128x128 = models.URLField(blank=True, null=True)
    photo_1024x1024 = models.URLField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Workspace(models.Model):
    """
    Workspace model based on Asana's Workspace schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=20, default='workspace')
    name = models.CharField(max_length=255)

    # Email domains associated with workspace
    email_domains = models.JSONField(default=list, blank=True)

    # Whether this is an organization
    is_organization = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspaces'

    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Team model based on Asana's Team schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='team')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    html_description = models.TextField(blank=True, null=True)

    # Organization this team belongs to (workspace that is_organization=True)
    organization = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='teams')

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'

    def __str__(self):
        return self.name


class Project(models.Model):
    """
    Project model based on Asana's Project schema
    """
    VIEW_CHOICES = [
        ('list', 'List'),
        ('board', 'Board'),
        ('calendar', 'Calendar'),
        ('timeline', 'Timeline'),
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='project')
    name = models.CharField(max_length=255)

    # Project status
    archived = models.BooleanField(default=False)
    color = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    html_notes = models.TextField(blank=True, null=True)

    # Dates
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    due_on = models.DateField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    start_on = models.DateField(blank=True, null=True)

    # View settings
    default_view = models.CharField(max_length=20, choices=VIEW_CHOICES, default='list')

    # Privacy
    public = models.BooleanField(default=False)  # True = public, False = private

    # Relationships
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='owned_projects')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True, related_name='projects')

    # Current status (simplified)
    current_status_color = models.CharField(max_length=20, blank=True, null=True)
    current_status_text = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Task model based on Asana's Task schema
    """
    SUBTYPE_CHOICES = [
        ('default_task', 'Default Task'),
        ('milestone', 'Milestone'),
        ('approval', 'Approval'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='task')
    name = models.CharField(max_length=255)

    # Task subtype
    resource_subtype = models.CharField(max_length=20, choices=SUBTYPE_CHOICES, default='default_task')

    # Status fields
    completed = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', blank=True, null=True)

    # Content
    notes = models.TextField(blank=True, null=True)
    html_notes = models.TextField(blank=True, null=True)

    # Dates
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    due_on = models.DateField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    start_on = models.DateField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)

    # Relationships
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_tasks')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='completed_tasks')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='subtasks')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tasks')
    projects = models.ManyToManyField(Project, related_name='tasks', blank=True)

    # Additional fields
    liked = models.BooleanField(default=False)
    num_likes = models.IntegerField(default=0)
    num_subtasks = models.IntegerField(default=0)

    class Meta:
        db_table = 'tasks'

    def __str__(self):
        return self.name


class Section(models.Model):
    """
    Section model for organizing tasks within projects
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='section')
    name = models.CharField(max_length=255)

    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sections')

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sections'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Tag model for categorizing tasks
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=5, default='tag')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=20, blank=True, null=True)

    # Relationships
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tags')

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.name


# Many-to-many relationship models
class TaskTag(models.Model):
    """
    Many-to-many relationship between tasks and tags
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'task_tags'
        unique_together = ['task', 'tag']


class ProjectMembership(models.Model):
    """
    Project membership for users
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=20, default='project_membership')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        db_table = 'project_memberships'
        unique_together = ['user', 'project']


class WorkspaceMembership(models.Model):
    """
    Workspace membership for users
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=20, default='workspace_membership')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)

    class Meta:
        db_table = 'workspace_memberships'
        unique_together = ['user', 'workspace']