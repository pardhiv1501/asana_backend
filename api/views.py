from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .models import (
    User, Workspace, Team, Project, Task, Section, Tag,
    ProjectMembership, WorkspaceMembership, TaskTag
)
from .serializers import (
    UserSerializer, WorkspaceSerializer, TeamSerializer, ProjectSerializer,
    TaskSerializer, SectionSerializer, TagSerializer,
    ProjectMembershipSerializer, WorkspaceMembershipSerializer,
    CreateUserSerializer, CreateWorkspaceSerializer, CreateTeamSerializer,
    CreateProjectSerializer, CreateTaskSerializer, CreateTagSerializer,
    AddProjectMembersSerializer, AddTaskFollowersSerializer
)


class AsanaPagination(PageNumberPagination):
    """Custom pagination class matching Asana's pagination"""
    page_size = 100
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return paginated response in Asana format"""
        return Response({
            'data': data,
            'next_page': self.get_next_link(),
            'prev_page': self.get_previous_link(),
        })


class AsanaModelViewSet(viewsets.ModelViewSet):
    """Base ViewSet that returns Asana-compatible responses"""
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """Override list to return Asana-style response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to return Asana-style response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        """Override create to return Asana-style response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Get the full serialized object using the read serializer
        instance = serializer.instance
        read_serializer = self.serializer_class(instance)
        return Response({'data': read_serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Override update to return Asana-style response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({'data': serializer.data})


class UserViewSet(AsanaModelViewSet):
    """ViewSet for User operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    def perform_create(self, serializer):
        # Generate a unique GID for the user
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        serializer.save(gid=gid)


class WorkspaceViewSet(AsanaModelViewSet):
    """ViewSet for Workspace operations"""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateWorkspaceSerializer
        return WorkspaceSerializer

    def perform_create(self, serializer):
        # Generate a unique GID for the workspace
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        serializer.save(gid=gid)

    @action(detail=True, methods=['get'])
    def teams(self, request, pk=None):
        """Get teams in this workspace"""
        workspace = self.get_object()
        teams = Team.objects.filter(organization=workspace)
        serializer = TeamSerializer(teams, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get projects in this workspace"""
        workspace = self.get_object()
        projects = Project.objects.filter(workspace=workspace)
        serializer = ProjectSerializer(projects, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get tasks in this workspace"""
        workspace = self.get_object()
        tasks = Task.objects.filter(workspace=workspace)
        serializer = TaskSerializer(tasks, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['get'])
    def tags(self, request, pk=None):
        """Get tags in this workspace"""
        workspace = self.get_object()
        tags = Tag.objects.filter(workspace=workspace)
        serializer = TagSerializer(tags, many=True)
        return Response({'data': serializer.data})


class TeamViewSet(AsanaModelViewSet):
    """ViewSet for Team operations"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTeamSerializer
        return TeamSerializer

    def perform_create(self, serializer):
        # Generate a unique GID and resolve organization
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        organization_gid = serializer.validated_data.pop('organization')
        organization = get_object_or_404(Workspace, gid=organization_gid)
        serializer.save(gid=gid, organization=organization)

    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get projects in this team"""
        team = self.get_object()
        projects = Project.objects.filter(team=team)
        serializer = ProjectSerializer(projects, many=True)
        return Response({'data': serializer.data})


class ProjectViewSet(AsanaModelViewSet):
    """ViewSet for Project operations"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProjectSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        # Generate a unique GID and resolve relationships
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)

        team_gid = serializer.validated_data.get('team')
        if team_gid:
            team = get_object_or_404(Team, gid=team_gid)
            serializer.validated_data['team'] = team

        owner_gid = serializer.validated_data.get('owner')
        if owner_gid:
            owner = get_object_or_404(User, gid=owner_gid)
            serializer.validated_data['owner'] = owner

        serializer.save(gid=gid, workspace=workspace)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get tasks in this project"""
        project = self.get_object()
        tasks = Task.objects.filter(projects=project)
        serializer = TaskSerializer(tasks, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['post'])
    def add_members(self, request, pk=None):
        """Add members to project"""
        project = self.get_object()
        serializer = AddProjectMembersSerializer(data=request.data)

        if serializer.is_valid():
            members_gids = serializer.validated_data['members']
            created_memberships = []

            for member_gid in members_gids:
                if member_gid == 'me':
                    # In a real implementation, this would use the authenticated user
                    continue

                user = get_object_or_404(User, gid=member_gid)

                # Create membership if it doesn't exist
                membership, created = ProjectMembership.objects.get_or_create(
                    user=user,
                    project=project,
                    defaults={'gid': str(uuid.uuid4().hex)[:16]}
                )

                if created:
                    membership_serializer = ProjectMembershipSerializer(membership)
                    created_memberships.append(membership_serializer.data)

            return Response({'data': created_memberships})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(AsanaModelViewSet):
    """ViewSet for Task operations"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTaskSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        # Generate a unique GID and resolve relationships
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)

        assignee_gid = serializer.validated_data.get('assignee')
        if assignee_gid:
            assignee = get_object_or_404(User, gid=assignee_gid)
            serializer.validated_data['assignee'] = assignee

        projects_gids = serializer.validated_data.pop('projects', [])
        projects = []
        for project_gid in projects_gids:
            project = get_object_or_404(Project, gid=project_gid)
            projects.append(project)

        # In a real implementation, created_by would be the authenticated user
        # For now, we'll set it to None or a default user
        task = serializer.save(gid=gid, workspace=workspace)
        task.projects.set(projects)
        return task

    def perform_update(self, serializer):
        """Handle task updates, especially completion"""
        task = self.get_object()
        old_completed = task.completed

        # Update assignee if provided
        assignee_gid = serializer.validated_data.get('assignee')
        if assignee_gid:
            assignee = get_object_or_404(User, gid=assignee_gid)
            serializer.validated_data['assignee'] = assignee

        task = serializer.save()

        # Handle completion tracking
        if task.completed and not old_completed:
            task.completed_at = timezone.now()
            # In a real implementation, completed_by would be the authenticated user
            task.save()

        return task

    @action(detail=True, methods=['post'])
    def add_followers(self, request, pk=None):
        """Add followers to task"""
        task = self.get_object()
        serializer = AddTaskFollowersSerializer(data=request.data)

        if serializer.is_valid():
            followers_gids = serializer.validated_data['followers']
            # In a real implementation, this would create follower relationships
            # For now, we'll just return success
            return Response({'data': []})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """Add a tag to the task"""
        task = self.get_object()
        tag_gid = request.data.get('tag')

        if not tag_gid:
            return Response({'errors': [{'message': 'tag field is required'}]}, status=status.HTTP_400_BAD_REQUEST)

        tag = get_object_or_404(Tag, gid=tag_gid)

        # Create relationship if it doesn't exist
        task_tag, created = TaskTag.objects.get_or_create(task=task, tag=tag)

        if created:
            return Response({'data': {'task': TaskSerializer(task).data}})
        else:
            return Response({'errors': [{'message': 'Tag already added to task'}]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_tag(self, request, pk=None):
        """Remove a tag from the task"""
        task = self.get_object()
        tag_gid = request.data.get('tag')

        if not tag_gid:
            return Response({'errors': [{'message': 'tag field is required'}]}, status=status.HTTP_400_BAD_REQUEST)

        tag = get_object_or_404(Tag, gid=tag_gid)

        # Remove relationship
        deleted_count, _ = TaskTag.objects.filter(task=task, tag=tag).delete()

        if deleted_count > 0:
            return Response({'data': {'task': TaskSerializer(task).data}})
        else:
            return Response({'errors': [{'message': 'Tag not found on task'}]}, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(AsanaModelViewSet):
    """ViewSet for Tag operations"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = AsanaPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTagSerializer
        return TagSerializer

    def perform_create(self, serializer):
        # Generate a unique GID and resolve workspace
        import uuid
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        serializer.save(gid=gid, workspace=workspace)


# Additional API views for specific endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
def user_me(request):
    """Get current user (me endpoint)"""
    # In a real implementation, this would return the authenticated user
    # For now, return a sample user or handle appropriately
    try:
        user = User.objects.first()
        if user:
            serializer = UserSerializer(user)
            return Response({'data': serializer.data})
        else:
            return Response({'errors': [{'message': 'No users found'}]}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'errors': [{'message': str(e)}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def workspace_projects(request, workspace_gid):
    """Get projects in a workspace (alternative endpoint)"""
    try:
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        projects = Project.objects.filter(workspace=workspace)
        serializer = ProjectSerializer(projects, many=True)
        return Response({'data': serializer.data})
    except Exception as e:
        return Response({'errors': [{'message': str(e)}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def workspace_tasks(request, workspace_gid):
    """Get tasks in a workspace (alternative endpoint)"""
    try:
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        tasks = Task.objects.filter(workspace=workspace)
        serializer = TaskSerializer(tasks, many=True)
        return Response({'data': serializer.data})
    except Exception as e:
        return Response({'errors': [{'message': str(e)}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def project_tasks(request, project_gid):
    """Get tasks in a project (alternative endpoint)"""
    try:
        project = get_object_or_404(Project, gid=project_gid)
        tasks = Task.objects.filter(projects=project)
        serializer = TaskSerializer(tasks, many=True)
        return Response({'data': serializer.data})
    except Exception as e:
        return Response({'errors': [{'message': str(e)}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)