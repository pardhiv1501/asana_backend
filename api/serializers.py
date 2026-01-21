from rest_framework import serializers
from .models import User, Workspace, Team, Project, Task, Section, Tag, ProjectMembership, WorkspaceMembership


class UserCompactSerializer(serializers.ModelSerializer):
    """Compact user serializer for nested relationships"""
    class Meta:
        model = User
        fields = ['gid', 'resource_type', 'name']


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer"""
    photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'gid', 'resource_type', 'name', 'email', 'photo',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']

    def get_photo(self, obj):
        """Return photo URLs in the format expected by Asana API"""
        photo_data = {}
        if obj.photo_21x21:
            photo_data['image_21x21'] = obj.photo_21x21
        if obj.photo_27x27:
            photo_data['image_27x27'] = obj.photo_27x27
        if obj.photo_36x36:
            photo_data['image_36x36'] = obj.photo_36x36
        if obj.photo_60x60:
            photo_data['image_60x60'] = obj.photo_60x60
        if obj.photo_128x128:
            photo_data['image_128x128'] = obj.photo_128x128
        if obj.photo_1024x1024:
            photo_data['image_1024x1024'] = obj.photo_1024x1024
        return photo_data if photo_data else None


class WorkspaceCompactSerializer(serializers.ModelSerializer):
    """Compact workspace serializer for nested relationships"""
    class Meta:
        model = Workspace
        fields = ['gid', 'resource_type', 'name']


class WorkspaceSerializer(serializers.ModelSerializer):
    """Full workspace serializer"""
    class Meta:
        model = Workspace
        fields = [
            'gid', 'resource_type', 'name', 'email_domains', 'is_organization',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']


class TeamCompactSerializer(serializers.ModelSerializer):
    """Compact team serializer"""
    organization = WorkspaceCompactSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ['gid', 'resource_type', 'name', 'organization']


class TeamSerializer(serializers.ModelSerializer):
    """Full team serializer"""
    organization = WorkspaceCompactSerializer(read_only=True)

    class Meta:
        model = Team
        fields = [
            'gid', 'resource_type', 'name', 'description', 'html_description',
            'organization', 'created_at', 'modified_at'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']


class ProjectCompactSerializer(serializers.ModelSerializer):
    """Compact project serializer for nested relationships"""
    class Meta:
        model = Project
        fields = ['gid', 'resource_type', 'name']


class ProjectSerializer(serializers.ModelSerializer):
    """Full project serializer"""
    workspace = WorkspaceCompactSerializer(read_only=True)
    owner = UserCompactSerializer(read_only=True)
    team = TeamCompactSerializer(read_only=True)
    current_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'gid', 'resource_type', 'name', 'archived', 'color', 'notes', 'html_notes',
            'created_at', 'modified_at', 'due_on', 'due_at', 'start_on', 'default_view',
            'public', 'workspace', 'owner', 'team', 'current_status'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']

    def get_current_status(self, obj):
        """Return current status in Asana format"""
        if obj.current_status_text or obj.current_status_color:
            return {
                'gid': f"status_{obj.gid}",
                'resource_type': 'project_status',
                'title': 'Current Status',
                'text': obj.current_status_text or '',
                'color': obj.current_status_color or 'green',
                'created_at': obj.created_at.isoformat(),
                'created_by': None,
                'modified_at': obj.modified_at.isoformat(),
            }
        return None


class TaskCompactSerializer(serializers.ModelSerializer):
    """Compact task serializer for nested relationships"""
    class Meta:
        model = Task
        fields = ['gid', 'resource_type', 'name']


class TaskSerializer(serializers.ModelSerializer):
    """Full task serializer"""
    assignee = UserCompactSerializer(read_only=True)
    created_by = UserCompactSerializer(read_only=True)
    completed_by = UserCompactSerializer(read_only=True)
    parent = TaskCompactSerializer(read_only=True)
    workspace = WorkspaceCompactSerializer(read_only=True)
    projects = ProjectCompactSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'gid', 'resource_type', 'name', 'resource_subtype', 'approval_status',
            'completed', 'notes', 'html_notes', 'created_at', 'modified_at',
            'completed_at', 'due_on', 'due_at', 'start_on', 'start_at',
            'assignee', 'created_by', 'completed_by', 'parent', 'workspace',
            'projects', 'liked', 'num_likes', 'num_subtasks', 'tags'
        ]
        read_only_fields = [
            'gid', 'resource_type', 'created_at', 'modified_at', 'completed_at',
            'created_by', 'completed_by', 'num_likes', 'num_subtasks'
        ]

    def get_tags(self, obj):
        """Get tags associated with this task"""
        from .models import TaskTag
        task_tags = TaskTag.objects.filter(task=obj).select_related('tag')
        tags_data = []
        for task_tag in task_tags:
            tag = task_tag.tag
            tags_data.append({
                'gid': tag.gid,
                'resource_type': tag.resource_type,
                'name': tag.name,
                'color': tag.color
            })
        return tags_data


class SectionCompactSerializer(serializers.ModelSerializer):
    """Compact section serializer"""
    class Meta:
        model = Section
        fields = ['gid', 'resource_type', 'name']


class SectionSerializer(serializers.ModelSerializer):
    """Full section serializer"""
    project = ProjectCompactSerializer(read_only=True)

    class Meta:
        model = Section
        fields = [
            'gid', 'resource_type', 'name', 'project',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    workspace = WorkspaceCompactSerializer(read_only=True)

    class Meta:
        model = Tag
        fields = [
            'gid', 'resource_type', 'name', 'color', 'workspace',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['gid', 'resource_type', 'created_at', 'modified_at']


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Project membership serializer"""
    user = UserCompactSerializer(read_only=True)
    project = ProjectCompactSerializer(read_only=True)

    class Meta:
        model = ProjectMembership
        fields = [
            'gid', 'resource_type', 'user', 'project'
        ]
        read_only_fields = ['gid', 'resource_type']


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    """Workspace membership serializer"""
    user = UserCompactSerializer(read_only=True)
    workspace = WorkspaceCompactSerializer(read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = [
            'gid', 'resource_type', 'user', 'workspace'
        ]
        read_only_fields = ['gid', 'resource_type']


# Request serializers for creating/updating resources
class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    class Meta:
        model = User
        fields = ['name', 'email']
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
        }


class CreateWorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for creating workspaces"""
    class Meta:
        model = Workspace
        fields = ['name', 'is_organization', 'email_domains']
        extra_kwargs = {
            'name': {'required': True},
        }


class CreateTeamSerializer(serializers.ModelSerializer):
    """Serializer for creating teams"""
    organization = serializers.CharField(write_only=True)

    class Meta:
        model = Team
        fields = ['name', 'description', 'organization']
        extra_kwargs = {
            'name': {'required': True},
            'organization': {'required': True},
        }


class CreateProjectSerializer(serializers.ModelSerializer):
    """Serializer for creating projects"""
    workspace = serializers.CharField(write_only=True)

    class Meta:
        model = Project
        fields = [
            'name', 'workspace', 'team', 'owner', 'color', 'notes',
            'due_on', 'start_on', 'public', 'default_view'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'workspace': {'required': True},
        }


class CreateTaskSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""
    workspace = serializers.CharField(write_only=True)
    projects = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Task
        fields = [
            'name', 'notes', 'assignee', 'workspace', 'projects',
            'due_on', 'start_on', 'resource_subtype'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'workspace': {'required': True},
        }


class CreateTagSerializer(serializers.ModelSerializer):
    """Serializer for creating tags"""
    workspace = serializers.CharField(write_only=True)

    class Meta:
        model = Tag
        fields = ['name', 'color', 'workspace']
        extra_kwargs = {
            'name': {'required': True},
            'workspace': {'required': True},
        }


class AddProjectMembersSerializer(serializers.Serializer):
    """Serializer for adding project members"""
    members = serializers.ListField(child=serializers.CharField(), required=True)

    def validate_members(self, value):
        """Validate that members exist"""
        from .models import User
        for member_gid in value:
            if member_gid != 'me':  # 'me' is a special identifier
                try:
                    User.objects.get(gid=member_gid)
                except User.DoesNotExist:
                    raise serializers.ValidationError(f"User with gid {member_gid} does not exist")
        return value


class AddTaskFollowersSerializer(serializers.Serializer):
    """Serializer for adding task followers"""
    followers = serializers.ListField(child=serializers.CharField(), required=True)

    def validate_followers(self, value):
        """Validate that followers exist"""
        from .models import User
        for follower_gid in value:
            if follower_gid != 'me':  # 'me' is a special identifier
                try:
                    User.objects.get(gid=follower_gid)
                except User.DoesNotExist:
                    raise serializers.ValidationError(f"User with gid {follower_gid} does not exist")
        return value