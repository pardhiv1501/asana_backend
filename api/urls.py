from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'workspaces', views.WorkspaceViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'tags', views.TagViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Additional endpoints
    path('users/me', views.user_me, name='user-me'),
    path('workspaces/<str:workspace_gid>/projects', views.workspace_projects, name='workspace-projects'),
    path('workspaces/<str:workspace_gid>/tasks', views.workspace_tasks, name='workspace-tasks'),
    path('projects/<str:project_gid>/tasks', views.project_tasks, name='project-tasks'),
]