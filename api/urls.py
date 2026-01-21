from django.urls import path
from . import views

urlpatterns = [
    # Users
    path('users/', views.UserListCreateView.as_view(), name='users-list-create'),
    path('users/<str:pk>/', views.UserDetailView.as_view(), name='users-detail'),
    path('users/me', views.UserMeView.as_view(), name='user-me'),

    # Workspaces and sub-resources
    path('workspaces/', views.WorkspaceListCreateView.as_view(), name='workspaces-list-create'),
    path('workspaces/<str:pk>/', views.WorkspaceDetailView.as_view(), name='workspaces-detail'),
    path('workspaces/<str:workspace_gid>/teams', views.WorkspaceTeamsView.as_view(), name='workspace-teams'),
    path('workspaces/<str:workspace_gid>/projects', views.WorkspaceProjectsView.as_view(), name='workspace-projects'),
    path('workspaces/<str:workspace_gid>/tasks', views.WorkspaceTasksView.as_view(), name='workspace-tasks'),
    path('workspaces/<str:workspace_gid>/tags', views.WorkspaceTagsView.as_view(), name='workspace-tags'),

    # Teams
    path('teams/', views.TeamListCreateView.as_view(), name='teams-list-create'),
    path('teams/<str:pk>/', views.TeamDetailView.as_view(), name='teams-detail'),
    path('teams/<str:team_gid>/projects', views.TeamProjectsView.as_view(), name='team-projects'),

    # Projects
    path('projects/', views.ProjectListCreateView.as_view(), name='projects-list-create'),
    path('projects/<str:pk>/', views.ProjectDetailView.as_view(), name='projects-detail'),
    path('projects/<str:project_gid>/tasks', views.ProjectTasksView.as_view(), name='project-tasks'),
    path('projects/<str:project_gid>/add_members', views.ProjectAddMembersView.as_view(), name='project-add-members'),

    # Tasks
    path('tasks/', views.TaskListCreateView.as_view(), name='tasks-list-create'),
    path('tasks/<str:pk>/', views.TaskDetailView.as_view(), name='tasks-detail'),
    path('tasks/<str:task_gid>/add_followers', views.TaskAddFollowersView.as_view(), name='task-add-followers'),
    path('tasks/<str:task_gid>/add_tag', views.TaskAddTagView.as_view(), name='task-add-tag'),
    path('tasks/<str:task_gid>/remove_tag', views.TaskRemoveTagView.as_view(), name='task-remove-tag'),

    # Tags
    path('tags/', views.TagListCreateView.as_view(), name='tags-list-create'),
    path('tags/<str:pk>/', views.TagDetailView.as_view(), name='tags-detail'),

    # Stories
    path('stories/', views.StoryListCreateView.as_view(), name='stories-list-create'),
    path('stories/<str:pk>/', views.StoryDetailView.as_view(), name='stories-detail'),

    # Attachments
    path('attachments/', views.AttachmentListCreateView.as_view(), name='attachments-list-create'),
    path('attachments/<str:pk>/', views.AttachmentDetailView.as_view(), name='attachments-detail'),

    # Custom fields
    path('custom_fields/', views.CustomFieldListCreateView.as_view(), name='custom-fields-list-create'),
    path('custom_fields/<str:pk>/', views.CustomFieldDetailView.as_view(), name='custom-fields-detail'),

    # Project statuses
    path('project_statuses/', views.ProjectStatusListCreateView.as_view(), name='project-statuses-list-create'),
    path('project_statuses/<str:pk>/', views.ProjectStatusDetailView.as_view(), name='project-statuses-detail'),

    # Webhooks
    path('webhooks/', views.WebhookListCreateView.as_view(), name='webhooks-list-create'),
    path('webhooks/<str:pk>/', views.WebhookDetailView.as_view(), name='webhooks-detail'),

    # Allocations
    path('allocations/', views.AllocationListCreateView.as_view(), name='allocations-list-create'),
    path('allocations/<str:pk>/', views.AllocationDetailView.as_view(), name='allocations-detail'),
]