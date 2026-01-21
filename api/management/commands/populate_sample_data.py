from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import User, Workspace, Team, Project, Task, Tag
import uuid


class Command(BaseCommand):
    help = 'Populate sample data for testing the Asana API'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample users
        user1 = User.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='John Doe',
            email='john.doe@example.com'
        )

        user2 = User.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Jane Smith',
            email='jane.smith@example.com'
        )

        user3 = User.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Bob Johnson',
            email='bob.johnson@example.com'
        )

        self.stdout.write(f'Created users: {user1.name}, {user2.name}, {user3.name}')

        # Create sample workspace
        workspace = Workspace.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Sample Company Workspace',
            is_organization=True,
            email_domains=['example.com']
        )

        self.stdout.write(f'Created workspace: {workspace.name}')

        # Create sample team
        team = Team.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Engineering Team',
            description='The engineering team for product development',
            organization=workspace
        )

        self.stdout.write(f'Created team: {team.name}')

        # Create sample projects
        project1 = Project.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Website Redesign',
            workspace=workspace,
            team=team,
            owner=user1,
            color='blue',
            notes='Complete redesign of the company website',
            due_on=timezone.now().date() + timezone.timedelta(days=30),
            public=False
        )

        project2 = Project.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Mobile App Development',
            workspace=workspace,
            team=team,
            owner=user2,
            color='green',
            notes='Develop the new mobile application',
            public=True
        )

        self.stdout.write(f'Created projects: {project1.name}, {project2.name}')

        # Create sample tags
        tag1 = Tag.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Urgent',
            color='red',
            workspace=workspace
        )

        tag2 = Tag.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Bug',
            color='orange',
            workspace=workspace
        )

        tag3 = Tag.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Feature',
            color='blue',
            workspace=workspace
        )

        self.stdout.write(f'Created tags: {tag1.name}, {tag2.name}, {tag3.name}')

        # Create sample tasks
        task1 = Task.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Design homepage mockups',
            workspace=workspace,
            assignee=user1,
            created_by=user1,
            notes='Create high-fidelity mockups for the new homepage design',
            due_on=timezone.now().date() + timezone.timedelta(days=7),
            resource_subtype='default_task'
        )
        task1.projects.add(project1)

        task2 = Task.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Implement user authentication',
            workspace=workspace,
            assignee=user2,
            created_by=user2,
            notes='Implement secure user authentication system',
            due_on=timezone.now().date() + timezone.timedelta(days=14),
            resource_subtype='default_task'
        )
        task2.projects.add(project2)

        task3 = Task.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            name='Fix login bug',
            workspace=workspace,
            assignee=user3,
            created_by=user1,
            notes='Users are unable to login with certain browsers',
            completed=True,
            completed_at=timezone.now(),
            resource_subtype='default_task'
        )
        task3.projects.add(project2)

        self.stdout.write(f'Created tasks: {task1.name}, {task2.name}, {task3.name}')

        # Create workspace memberships
        from api.models import WorkspaceMembership
        WorkspaceMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user1,
            workspace=workspace
        )
        WorkspaceMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user2,
            workspace=workspace
        )
        WorkspaceMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user3,
            workspace=workspace
        )

        # Create project memberships
        from api.models import ProjectMembership
        ProjectMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user1,
            project=project1
        )
        ProjectMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user2,
            project=project1
        )
        ProjectMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user2,
            project=project2
        )
        ProjectMembership.objects.create(
            gid=str(uuid.uuid4().hex)[:16],
            user=user3,
            project=project2
        )

        self.stdout.write('Sample data created successfully!')
        self.stdout.write('You can now test the API endpoints.')
        self.stdout.write(f'Sample workspace GID: {workspace.gid}')
        self.stdout.write(f'Sample project GID: {project1.gid}')
        self.stdout.write(f'Sample task GID: {task1.gid}')