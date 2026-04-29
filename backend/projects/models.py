from django.db import models
from django.conf import settings

ROLE_RANK = {'owner': 3, 'admin': 2, 'editor': 1, 'viewer': 0}


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = 'private', 'Private'
        PUBLIC  = 'public',  'Public'

    owner      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects',
    )
    name       = models.CharField(max_length=255)
    visibility = models.CharField(
        max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE,
    )
    tags       = models.ManyToManyField(Tag, blank=True, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.owner})"


class ProjectMember(models.Model):
    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Admin'
        EDITOR = 'editor', 'Edytor'
        VIEWER = 'viewer', 'Widz'

    project  = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships',
    )
    role     = models.CharField(max_length=10, choices=Role.choices)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='added_members',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.user} – {self.role} in {self.project}"


class ProjectInvite(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Oczekuje'
        ACCEPTED  = 'accepted',  'Zaakceptowane'
        DECLINED  = 'declined',  'Odrzucone'
        CANCELLED = 'cancelled', 'Anulowane'

    project      = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invites')
    invited_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invites',
    )
    invitee      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invites',
    )
    role         = models.CharField(max_length=10, choices=ProjectMember.Role.choices)
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at   = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite: {self.invitee} → {self.project} as {self.role} [{self.status}]"
