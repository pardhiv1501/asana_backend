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
    User model based on Asana's User schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='user')
    name = models.CharField(max_length=255)

    # Email field - not unique as per Asana API (users can have multiple emails)
    email = models.EmailField()

    # Photo fields as per Asana API spec
    photo = models.JSONField(blank=True, null=True)  # Stores photo URLs in various sizes

    # Workspaces this user belongs to (many-to-many through WorkspaceMembership)
    workspaces = models.ManyToManyField('Workspace', through='WorkspaceMembership', related_name='users')

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


class Story(models.Model):
    """
    Story model for task comments/updates based on Asana's Story schema
    """
    STORY_TYPE_CHOICES = [
        ('comment', 'Comment'),
        ('system', 'System'),
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='story')
    resource_subtype = models.CharField(max_length=20, choices=STORY_TYPE_CHOICES, default='comment')

    # Story content
    text = models.TextField(blank=True, null=True)
    html_text = models.TextField(blank=True, null=True)

    # Relationships
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='stories')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_stories')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stories'
        ordering = ['created_at']

    def __str__(self):
        return f"Story on {self.task.name}"


class Attachment(models.Model):
    """
    Attachment model based on Asana's Attachment schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=15, default='attachment')

    name = models.CharField(max_length=255)
    resource_subtype = models.CharField(max_length=20, default='external')  # 'external' or 'asana'

    # File information
    size = models.PositiveIntegerField(blank=True, null=True)
    download_url = models.URLField(blank=True, null=True)
    view_url = models.URLField(blank=True, null=True)
    permanent_url = models.URLField(blank=True, null=True)

    # Relationships
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_attachments')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attachments'

    def __str__(self):
        return self.name


class CustomField(models.Model):
    """
    Custom field model based on Asana's CustomField schema
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('enum', 'Enum'),
        ('multi_enum', 'Multi-Enum'),
        ('date', 'Date'),
        ('people', 'People'),
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=15, default='custom_field')

    name = models.CharField(max_length=255)
    resource_subtype = models.CharField(max_length=15, choices=FIELD_TYPE_CHOICES, default='text')
    type = models.CharField(max_length=15, choices=FIELD_TYPE_CHOICES, default='text')  # Alias for resource_subtype

    description = models.TextField(blank=True, null=True)

    # For enum fields
    enum_options = models.JSONField(blank=True, null=True)

    # Relationships
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='custom_fields')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_custom_fields')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_fields'

    def __str__(self):
        return self.name


class CustomFieldValue(models.Model):
    """
    Custom field value for tasks/projects
    """
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)

    # The value - can be text, number, date, or JSON for complex types
    text_value = models.TextField(blank=True, null=True)
    number_value = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    date_value = models.DateField(blank=True, null=True)
    enum_value = models.CharField(max_length=255, blank=True, null=True)  # For enum options

    class Meta:
        db_table = 'custom_field_values'
        unique_together = [
            ('custom_field', 'task'),
            ('custom_field', 'project'),
        ]


class ProjectStatus(models.Model):
    """
    Project status model based on Asana's ProjectStatus schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=15, default='project_status')

    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    html_text = models.TextField(blank=True, null=True)

    COLOR_CHOICES = [
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('red', 'Red'),
        ('blue', 'Blue'),
    ]
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='green')

    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='statuses')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_project_statuses')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_statuses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.title}"


class Event(models.Model):
    """
    Event model for workspace activity based on Asana's Event schema
    """
    EVENT_TYPE_CHOICES = [
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_deleted', 'Task Deleted'),
        ('project_created', 'Project Created'),
        ('project_updated', 'Project Updated'),
        ('project_deleted', 'Project Deleted'),
        ('comment_added', 'Comment Added'),
        # Add more as needed
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='event')

    action = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    resource = models.JSONField()  # The resource that changed
    change = models.JSONField(blank=True, null=True)  # What changed
    parent = models.JSONField(blank=True, null=True)  # Parent resource info

    # Relationships
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='events')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='events')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'events'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} by {self.user}"


class Webhook(models.Model):
    """
    Webhook model based on Asana's Webhook schema
    """
    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=10, default='webhook')

    # Webhook configuration
    callback_url = models.URLField()
    method = models.CharField(max_length=10, default='POST')

    # Filters for what events to send
    filters = models.JSONField(default=list)

    # Relationships
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='webhooks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_webhooks')

    # Status
    active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks'

    def __str__(self):
        return f"Webhook to {self.callback_url}"


class Allocation(models.Model):
    """
    Allocation model based on Asana's Allocation schema.
    Represents how much of a resource is allocated to a work object
    over a specific period with an effort value (percentage or hours).
    """

    EFFORT_UNIT_CHOICES = [
        ('percentage', 'Percentage'),
        ('hours', 'Hours'),
    ]

    gid = models.CharField(max_length=20, unique=True, primary_key=True)
    resource_type = models.CharField(max_length=15, default='allocation')

    # What is being allocated (e.g., person, team)
    resource = models.JSONField()  # store compact resource ref {gid, resource_type, name}
    # Work object receiving the allocation (e.g., project, portfolio)
    work_object = models.JSONField()  # store compact object ref {gid, resource_type, name}

    effort_value = models.DecimalField(max_digits=8, decimal_places=2)
    effort_unit = models.CharField(max_length=20, choices=EFFORT_UNIT_CHOICES, default='percentage')

    start_on = models.DateField()
    end_on = models.DateField(blank=True, null=True)

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='allocations')

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'allocations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Allocation {self.gid}"