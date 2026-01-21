from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import (
    User, Workspace, Team, Project, Task, Section, Tag,
    ProjectMembership, WorkspaceMembership, TaskTag,
    Story, Attachment, CustomField, ProjectStatus, Event, Webhook,
    Allocation
)
from .serializers import (
    UserSerializer, WorkspaceSerializer, TeamSerializer, ProjectSerializer,
    TaskSerializer, SectionSerializer, TagSerializer,
    ProjectMembershipSerializer, WorkspaceMembershipSerializer,
    StorySerializer, AttachmentSerializer, CustomFieldSerializer,
    ProjectStatusSerializer, EventSerializer, WebhookSerializer,
    AllocationSerializer,
    CreateUserSerializer, CreateWorkspaceSerializer, CreateTeamSerializer,
    CreateProjectSerializer, CreateTaskSerializer, CreateTagSerializer,
    CreateStorySerializer, CreateAttachmentSerializer, CreateCustomFieldSerializer,
    CreateProjectStatusSerializer, CreateWebhookSerializer,
    CreateAllocationSerializer,
    AddProjectMembersSerializer, AddTaskFollowersSerializer
)
import uuid


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


class AsanaListCreateAPIView(generics.ListCreateAPIView):
    """Base List/Create API with Asana-style responses"""
    permission_classes = [AllowAny]
    pagination_class = AsanaPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = self.get_serializer(instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response({'data': read_serializer.data}, status=status.HTTP_201_CREATED, headers=headers)


class AsanaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Base Retrieve/Update/Destroy API with Asana-style responses"""
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'data': serializer.data})

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


# User views
class UserListCreateView(AsanaListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        return CreateUserSerializer if self.request.method == 'POST' else UserSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        serializer.save(gid=gid)


class UserDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserMeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = User.objects.first()
        if not user:
            return Response({'errors': [{'message': 'No users found'}]}, status=status.HTTP_404_NOT_FOUND)
        return Response({'data': UserSerializer(user).data})


# Workspace views
class WorkspaceListCreateView(AsanaListCreateAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get_serializer_class(self):
        return CreateWorkspaceSerializer if self.request.method == 'POST' else WorkspaceSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        serializer.save(gid=gid)


class WorkspaceDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer


class WorkspaceTeamsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, workspace_gid):
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        teams = Team.objects.filter(organization=workspace)
        return Response({'data': TeamSerializer(teams, many=True).data})


class WorkspaceProjectsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, workspace_gid):
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        projects = Project.objects.filter(workspace=workspace)
        return Response({'data': ProjectSerializer(projects, many=True).data})


class WorkspaceTasksView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, workspace_gid):
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        tasks = Task.objects.filter(workspace=workspace)
        return Response({'data': TaskSerializer(tasks, many=True).data})


class WorkspaceTagsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, workspace_gid):
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        tags = Tag.objects.filter(workspace=workspace)
        return Response({'data': TagSerializer(tags, many=True).data})


# Team views
class TeamListCreateView(AsanaListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_serializer_class(self):
        return CreateTeamSerializer if self.request.method == 'POST' else TeamSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        organization_gid = serializer.validated_data.pop('organization')
        organization = get_object_or_404(Workspace, gid=organization_gid)
        serializer.save(gid=gid, organization=organization)


class TeamDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class TeamProjectsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, team_gid):
        team = get_object_or_404(Team, gid=team_gid)
        projects = Project.objects.filter(team=team)
        return Response({'data': ProjectSerializer(projects, many=True).data})


# Project views
class ProjectListCreateView(AsanaListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_serializer_class(self):
        return CreateProjectSerializer if self.request.method == 'POST' else ProjectSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        team_gid = serializer.validated_data.get('team')
        if team_gid:
            serializer.validated_data['team'] = get_object_or_404(Team, gid=team_gid)
        owner_gid = serializer.validated_data.get('owner')
        if owner_gid:
            serializer.validated_data['owner'] = get_object_or_404(User, gid=owner_gid)
        serializer.save(gid=gid, workspace=workspace)


class ProjectDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectTasksView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, project_gid):
        project = get_object_or_404(Project, gid=project_gid)
        tasks = Task.objects.filter(projects=project)
        return Response({'data': TaskSerializer(tasks, many=True).data})


class ProjectAddMembersView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, project_gid):
        project = get_object_or_404(Project, gid=project_gid)
        serializer = AddProjectMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        members_gids = serializer.validated_data['members']
        created_memberships = []
        for member_gid in members_gids:
            if member_gid == 'me':
                continue
            user = get_object_or_404(User, gid=member_gid)
            membership, created = ProjectMembership.objects.get_or_create(
                user=user,
                project=project,
                defaults={'gid': str(uuid.uuid4().hex)[:16]}
            )
            if created:
                created_memberships.append(ProjectMembershipSerializer(membership).data)
        return Response({'data': created_memberships})


# Task views
class TaskListCreateView(AsanaListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_serializer_class(self):
        return CreateTaskSerializer if self.request.method == 'POST' else TaskSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        assignee_gid = serializer.validated_data.get('assignee')
        if assignee_gid:
            serializer.validated_data['assignee'] = get_object_or_404(User, gid=assignee_gid)
        projects_gids = serializer.validated_data.pop('projects', [])
        projects = [get_object_or_404(Project, gid=pid) for pid in projects_gids]
        task = serializer.save(gid=gid, workspace=workspace)
        task.projects.set(projects)
        return task


class TaskDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_update(self, serializer):
        task = self.get_object()
        old_completed = task.completed
        assignee_gid = serializer.validated_data.get('assignee')
        if assignee_gid:
            serializer.validated_data['assignee'] = get_object_or_404(User, gid=assignee_gid)
        task = serializer.save()
        if task.completed and not old_completed:
            task.completed_at = timezone.now()
            task.save()
        return task


class TaskAddFollowersView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, task_gid):
        task = get_object_or_404(Task, gid=task_gid)
        serializer = AddTaskFollowersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Placeholder: would create follower relationships
        return Response({'data': []})


class TaskAddTagView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, task_gid):
        task = get_object_or_404(Task, gid=task_gid)
        tag_gid = request.data.get('tag')
        if not tag_gid:
            return Response({'errors': [{'message': 'tag field is required'}]}, status=status.HTTP_400_BAD_REQUEST)
        tag = get_object_or_404(Tag, gid=tag_gid)
        task_tag, created = TaskTag.objects.get_or_create(task=task, tag=tag)
        if created:
            return Response({'data': {'task': TaskSerializer(task).data}})
        return Response({'errors': [{'message': 'Tag already added to task'}]}, status=status.HTTP_400_BAD_REQUEST)


class TaskRemoveTagView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, task_gid):
        task = get_object_or_404(Task, gid=task_gid)
        tag_gid = request.data.get('tag')
        if not tag_gid:
            return Response({'errors': [{'message': 'tag field is required'}]}, status=status.HTTP_400_BAD_REQUEST)
        tag = get_object_or_404(Tag, gid=tag_gid)
        deleted_count, _ = TaskTag.objects.filter(task=task, tag=tag).delete()
        if deleted_count > 0:
            return Response({'data': {'task': TaskSerializer(task).data}})
        return Response({'errors': [{'message': 'Tag not found on task'}]}, status=status.HTTP_400_BAD_REQUEST)


# Tag views
class TagListCreateView(AsanaListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_serializer_class(self):
        return CreateTagSerializer if self.request.method == 'POST' else TagSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        serializer.save(gid=gid, workspace=workspace)


class TagDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# Story views
class StoryListCreateView(AsanaListCreateAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

    def get_serializer_class(self):
        return CreateStorySerializer if self.request.method == 'POST' else StorySerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        task_gid = serializer.validated_data.pop('task')
        task = get_object_or_404(Task, gid=task_gid)
        serializer.save(gid=gid, task=task)


class StoryDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer


# Attachment views
class AttachmentListCreateView(AsanaListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def get_serializer_class(self):
        return CreateAttachmentSerializer if self.request.method == 'POST' else AttachmentSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        task_gid = serializer.validated_data.pop('task')
        task = get_object_or_404(Task, gid=task_gid)
        serializer.save(gid=gid, task=task)


class AttachmentDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


# Custom field views
class CustomFieldListCreateView(AsanaListCreateAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer

    def get_serializer_class(self):
        return CreateCustomFieldSerializer if self.request.method == 'POST' else CustomFieldSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        serializer.save(gid=gid, workspace=workspace)


class CustomFieldDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer


# Project status views
class ProjectStatusListCreateView(AsanaListCreateAPIView):
    queryset = ProjectStatus.objects.all()
    serializer_class = ProjectStatusSerializer

    def get_serializer_class(self):
        return CreateProjectStatusSerializer if self.request.method == 'POST' else ProjectStatusSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        project_gid = serializer.validated_data.pop('project')
        project = get_object_or_404(Project, gid=project_gid)
        serializer.save(gid=gid, project=project)


class ProjectStatusDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = ProjectStatus.objects.all()
    serializer_class = ProjectStatusSerializer


# Webhook views
class WebhookListCreateView(AsanaListCreateAPIView):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer

    def get_serializer_class(self):
        return CreateWebhookSerializer if self.request.method == 'POST' else WebhookSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        serializer.save(gid=gid, workspace=workspace)


class WebhookDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer


# Allocation views
class AllocationListCreateView(AsanaListCreateAPIView):
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer

    def get_serializer_class(self):
        return CreateAllocationSerializer if self.request.method == 'POST' else AllocationSerializer

    def perform_create(self, serializer):
        gid = str(uuid.uuid4().hex)[:16]
        workspace_gid = serializer.validated_data.pop('workspace')
        workspace = get_object_or_404(Workspace, gid=workspace_gid)
        serializer.save(gid=gid, workspace=workspace)


class AllocationDetailView(AsanaRetrieveUpdateDestroyAPIView):
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer