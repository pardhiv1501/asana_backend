from django.contrib import admin

from .models import (
    User,
    Workspace,
    Team,
    Project,
    Task,
    Section,
    Tag,
    TaskTag,
    ProjectMembership,
    WorkspaceMembership,
    Story,
    Attachment,
    CustomField,
    CustomFieldValue,
    ProjectStatus,
    Event,
    Webhook,
    Allocation,
)


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = (
        'gid',
        'resource_type',
        'effort_value',
        'effort_unit',
        'start_on',
        'end_on',
        'workspace',
        'created_at',
        'modified_at',
    )
    list_filter = ('effort_unit', 'workspace')
    search_fields = ('gid',)


# Register remaining models (basic admin)
admin.site.register(User)
admin.site.register(Workspace)
admin.site.register(Team)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Section)
admin.site.register(Tag)
admin.site.register(TaskTag)
admin.site.register(ProjectMembership)
admin.site.register(WorkspaceMembership)
admin.site.register(Story)
admin.site.register(Attachment)
admin.site.register(CustomField)
admin.site.register(CustomFieldValue)
admin.site.register(ProjectStatus)
admin.site.register(Event)
admin.site.register(Webhook)
