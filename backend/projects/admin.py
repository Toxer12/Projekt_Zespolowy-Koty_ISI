from django.contrib import admin
from projects.models import Project, Tag, ProjectMember, ProjectInvite, ProjectFavorite


class ProjectMemberInline(admin.TabularInline):
    model           = ProjectMember
    extra           = 0
    fields          = ('user', 'role', 'added_by', 'added_at')
    readonly_fields = ('added_at',)


class ProjectInviteInline(admin.TabularInline):
    model           = ProjectInvite
    extra           = 0
    fields          = ('invitee', 'role', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display      = ('name', 'owner', 'visibility', 'created_at')
    list_filter       = ('visibility',)
    search_fields     = ('name', 'owner__email')
    readonly_fields   = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('tags',)
    inlines           = [ProjectMemberInline, ProjectInviteInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display  = ('user', 'project', 'role', 'added_at')
    list_filter   = ('role',)
    search_fields = ('user__email', 'project__name')


@admin.register(ProjectInvite)
class ProjectInviteAdmin(admin.ModelAdmin):
    list_display    = ('invitee', 'project', 'role', 'status', 'created_at')
    list_filter     = ('status', 'role')
    search_fields   = ('invitee__email', 'project__name')
    readonly_fields = ('id', 'created_at', 'responded_at')


@admin.register(ProjectFavorite)
class ProjectFavoriteAdmin(admin.ModelAdmin):
    list_display  = ('user', 'project', 'created_at')
    search_fields = ('user__email', 'project__name')