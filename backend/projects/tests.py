from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, Tag, ProjectMember, ProjectInvite, ROLE_RANK

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email, password='Pass1234x', username=None, is_active=True):
    username = username or email.split('@')[0]
    user = User.objects.create_user(email=email, password=password, username=username)
    user.is_active = is_active
    user.save()
    return user


def auth_client(user):
    """Return an APIClient with JWT access cookie set for *user*."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies['access_token'] = str(refresh.access_token)
    return client


def make_project(owner, name='Test Project', visibility='private'):
    return Project.objects.create(owner=owner, name=name, visibility=visibility)


def add_member(project, user, role, added_by=None):
    return ProjectMember.objects.create(
        project=project, user=user, role=role,
        added_by=added_by or project.owner,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class ProjectModelTests(TestCase):

    def setUp(self):
        self.owner = make_user('owner@test.com')

    def test_project_str(self):
        p = make_project(self.owner, 'My Project')
        self.assertIn('My Project', str(p))

    def test_project_default_visibility_is_private(self):
        p = Project.objects.create(owner=self.owner, name='P')
        self.assertEqual(p.visibility, 'private')

    def test_tag_str(self):
        tag = Tag.objects.create(name='python')
        self.assertEqual(str(tag), 'python')

    def test_project_member_str(self):
        p = make_project(self.owner)
        member_user = make_user('member@test.com')
        m = add_member(p, member_user, 'editor')
        self.assertIn('editor', str(m))

    def test_project_invite_str(self):
        p = make_project(self.owner)
        invitee = make_user('inv@test.com')
        invite = ProjectInvite.objects.create(
            project=p, invited_by=self.owner, invitee=invitee, role='editor'
        )
        self.assertIn('editor', str(invite))

    def test_role_rank_ordering(self):
        self.assertGreater(ROLE_RANK['owner'], ROLE_RANK['admin'])
        self.assertGreater(ROLE_RANK['admin'], ROLE_RANK['editor'])
        self.assertGreater(ROLE_RANK['editor'], ROLE_RANK['viewer'])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

class ProjectListCreateViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('owner@proj.com')
        self.client = auth_client(self.owner)
        self.url = '/api/projects/'

    def test_create_project(self):
        resp = self.client.post(self.url, {'name': 'New Project', 'visibility': 'private'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['name'], 'New Project')
        self.assertTrue(Project.objects.filter(name='New Project').exists())

    def test_create_project_with_tags(self):
        resp = self.client.post(
            self.url,
            {'name': 'Tagged', 'visibility': 'private', 'tags': ['python', 'django']},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn('python', resp.data['tags'])

    def test_list_own_projects(self):
        make_project(self.owner, 'P1')
        make_project(self.owner, 'P2')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_list_does_not_include_other_users_projects(self):
        other = make_user('other@proj.com')
        make_project(other, 'OtherProject')
        resp = self.client.get(self.url)
        names = [p['name'] for p in resp.data]
        self.assertNotIn('OtherProject', names)

    def test_unauthenticated_cannot_list(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_filter_by_visibility(self):
        make_project(self.owner, 'PubProj', visibility='public')
        make_project(self.owner, 'PrivProj', visibility='private')
        resp = self.client.get(self.url + '?visibility=public')
        self.assertEqual(resp.status_code, 200)
        names = [p['name'] for p in resp.data]
        self.assertIn('PubProj', names)
        self.assertNotIn('PrivProj', names)

    def test_create_project_missing_name(self):
        resp = self.client.post(self.url, {'visibility': 'private'})
        self.assertEqual(resp.status_code, 400)


class ProjectDetailViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('detowner@proj.com')
        self.client = auth_client(self.owner)
        self.project = make_project(self.owner, 'Detail Project')
        self.url = f'/api/projects/{self.project.pk}/'

    def test_get_own_project(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'Detail Project')

    def test_update_own_project(self):
        resp = self.client.patch(self.url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Name')

    def test_delete_own_project(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_member_cannot_delete_project(self):
        member = make_user('mem@proj.com')
        add_member(self.project, member, 'editor')
        c = auth_client(member)
        resp = c.delete(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_member_cannot_update_project(self):
        member = make_user('mem2@proj.com')
        add_member(self.project, member, 'admin')
        c = auth_client(member)
        resp = c.patch(self.url, {'name': 'Hacked'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_stranger_cannot_access_private_project(self):
        stranger = make_user('stranger@proj.com')
        c = auth_client(stranger)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 404)

    def test_member_can_view_project(self):
        viewer = make_user('viewer@proj.com')
        add_member(self.project, viewer, 'viewer')
        c = auth_client(viewer)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)


class PublicProjectListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('pubowner@proj.com')
        self.url = '/api/projects/public/'

    def test_public_projects_visible_to_any_authenticated_user(self):
        make_project(self.owner, 'PubP', visibility='public')
        other = make_user('other2@proj.com')
        c = auth_client(other)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        names = [p['name'] for p in resp.data]
        self.assertIn('PubP', names)

    def test_private_projects_not_in_public_list(self):
        make_project(self.owner, 'PrivP', visibility='private')
        c = auth_client(self.owner)
        resp = c.get(self.url)
        names = [p['name'] for p in resp.data]
        self.assertNotIn('PrivP', names)

    def test_unauthenticated_cannot_access(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)


class MemberProjectListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('sowner@proj.com')
        self.member = make_user('smember@proj.com')
        self.project = make_project(self.owner, 'Shared Project')
        add_member(self.project, self.member, 'editor')
        self.url = '/api/projects/shared/'

    def test_member_sees_shared_project(self):
        c = auth_client(self.member)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        names = [p['name'] for p in resp.data]
        self.assertIn('Shared Project', names)

    def test_owner_not_listed_in_shared(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        names = [p['name'] for p in resp.data]
        self.assertNotIn('Shared Project', names)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

class TagListViewTests(TestCase):

    def setUp(self):
        self.user = make_user('taguser@proj.com')
        self.client = auth_client(self.user)
        self.url = '/api/tags/'

    def test_list_tags(self):
        Tag.objects.create(name='alpha')
        Tag.objects.create(name='beta')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        names = [t['name'] for t in resp.data]
        self.assertIn('alpha', names)
        self.assertIn('beta', names)

    def test_unauthenticated_cannot_list_tags(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

class ProjectMemberListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('mowner@proj.com')
        self.project = make_project(self.owner, 'MemberProj')
        self.member = make_user('memlist@proj.com')
        add_member(self.project, self.member, 'editor')
        self.url = f'/api/projects/{self.project.pk}/members/'

    def test_owner_can_list_members(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # Should include owner entry + members
        self.assertGreaterEqual(len(resp.data), 2)

    def test_member_can_list_members(self):
        c = auth_client(self.member)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_stranger_cannot_list_members(self):
        stranger = make_user('stranger2@proj.com')
        c = auth_client(stranger)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_owner_appears_first_with_owner_role(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]['role'], 'owner')


class ProjectMemberUpdateViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('upowner@proj.com')
        self.project = make_project(self.owner, 'UpProj')
        self.editor = make_user('upeditor@proj.com')
        self.membership = add_member(self.project, self.editor, 'editor')
        self.url = f'/api/projects/{self.project.pk}/members/{self.editor.pk}/'

    def test_owner_can_change_member_role(self):
        c = auth_client(self.owner)
        resp = c.patch(self.url, {'role': 'viewer'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.role, 'viewer')

    def test_owner_can_remove_member(self):
        c = auth_client(self.owner)
        resp = c.delete(self.url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(ProjectMember.objects.filter(pk=self.membership.pk).exists())

    def test_editor_cannot_manage_same_level(self):
        editor2 = make_user('editor2@proj.com')
        add_member(self.project, editor2, 'editor')
        c = auth_client(self.editor)
        url = f'/api/projects/{self.project.pk}/members/{editor2.pk}/'
        resp = c.patch(url, {'role': 'viewer'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_invalid_role_returns_400(self):
        c = auth_client(self.owner)
        resp = c.patch(self.url, {'role': 'superadmin'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_stranger_cannot_manage_members(self):
        stranger = make_user('str3@proj.com')
        c = auth_client(stranger)
        resp = c.patch(self.url, {'role': 'viewer'}, format='json')
        self.assertEqual(resp.status_code, 404)


class LeaveProjectViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('leaveown@proj.com')
        self.project = make_project(self.owner, 'LeaveProj')
        self.member = make_user('leavemem@proj.com')
        add_member(self.project, self.member, 'editor')
        self.url = f'/api/projects/{self.project.pk}/leave/'

    def test_member_can_leave_project(self):
        c = auth_client(self.member)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(
            ProjectMember.objects.filter(project=self.project, user=self.member).exists()
        )

    def test_owner_cannot_leave_project(self):
        c = auth_client(self.owner)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_non_member_cannot_leave(self):
        stranger = make_user('leavestr@proj.com')
        c = auth_client(stranger)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------

class ProjectInviteCreateViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('invown@proj.com', username='invown')
        self.project = make_project(self.owner, 'InvProj')
        self.invitee = make_user('invitee@proj.com', username='inviteeuser')
        self.url = f'/api/projects/{self.project.pk}/members/invite/'

    def test_owner_can_invite_user(self):
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'inviteeuser', 'role': 'editor'})
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            ProjectInvite.objects.filter(project=self.project, invitee=self.invitee).exists()
        )

    def test_cannot_invite_self(self):
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'invown', 'role': 'editor'})
        self.assertEqual(resp.status_code, 400)

    def test_cannot_invite_nonexistent_user(self):
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'ghost999', 'role': 'editor'})
        self.assertEqual(resp.status_code, 404)

    def test_cannot_invite_invalid_role(self):
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'inviteeuser', 'role': 'superadmin'})
        self.assertEqual(resp.status_code, 400)

    def test_cannot_duplicate_pending_invite(self):
        ProjectInvite.objects.create(
            project=self.project, invited_by=self.owner,
            invitee=self.invitee, role='editor',
        )
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'inviteeuser', 'role': 'editor'})
        self.assertEqual(resp.status_code, 400)

    def test_cannot_invite_existing_member(self):
        add_member(self.project, self.invitee, 'editor')
        c = auth_client(self.owner)
        resp = c.post(self.url, {'username': 'inviteeuser', 'role': 'viewer'})
        self.assertEqual(resp.status_code, 400)

    def test_viewer_cannot_invite(self):
        viewer = make_user('viewer2@proj.com', username='viewer2user')
        add_member(self.project, viewer, 'viewer')
        c = auth_client(viewer)
        resp = c.post(self.url, {'username': 'inviteeuser', 'role': 'viewer'})
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_invite_editor(self):
        admin = make_user('admin2@proj.com', username='admin2user')
        add_member(self.project, admin, 'admin')
        invitee2 = make_user('inv2@proj.com', username='inv2user')
        c = auth_client(admin)
        resp = c.post(self.url, {'username': 'inv2user', 'role': 'editor'})
        self.assertEqual(resp.status_code, 201)

    def test_admin_cannot_invite_admin(self):
        admin = make_user('admin3@proj.com', username='admin3user')
        add_member(self.project, admin, 'admin')
        invitee3 = make_user('inv3@proj.com', username='inv3user')
        c = auth_client(admin)
        resp = c.post(self.url, {'username': 'inv3user', 'role': 'admin'})
        self.assertEqual(resp.status_code, 400)


class InviteRespondViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('resown@proj.com', username='resown')
        self.project = make_project(self.owner, 'ResProj')
        self.invitee = make_user('resitee@proj.com', username='resitee')
        self.invite = ProjectInvite.objects.create(
            project=self.project, invited_by=self.owner,
            invitee=self.invitee, role='editor',
        )
        self.url = f'/api/invites/{self.invite.pk}/respond/'

    def test_invitee_can_accept(self):
        c = auth_client(self.invitee)
        resp = c.post(self.url, {'action': 'accept'})
        self.assertEqual(resp.status_code, 200)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, 'accepted')
        self.assertTrue(
            ProjectMember.objects.filter(project=self.project, user=self.invitee).exists()
        )

    def test_invitee_can_decline(self):
        c = auth_client(self.invitee)
        resp = c.post(self.url, {'action': 'decline'})
        self.assertEqual(resp.status_code, 200)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, 'declined')

    def test_invalid_action_returns_400(self):
        c = auth_client(self.invitee)
        resp = c.post(self.url, {'action': 'maybe'})
        self.assertEqual(resp.status_code, 400)

    def test_cannot_respond_to_non_pending_invite(self):
        self.invite.status = 'declined'
        self.invite.save()
        c = auth_client(self.invitee)
        resp = c.post(self.url, {'action': 'accept'})
        self.assertEqual(resp.status_code, 400)

    def test_other_user_cannot_respond_to_invite(self):
        other = make_user('other3@proj.com')
        c = auth_client(other)
        resp = c.post(self.url, {'action': 'accept'})
        self.assertEqual(resp.status_code, 404)


class InviteListViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('listinvown@proj.com', username='listinvown')
        self.project = make_project(self.owner, 'ListInvProj')
        self.invitee = make_user('listinvitee@proj.com', username='listinvitee')
        ProjectInvite.objects.create(
            project=self.project, invited_by=self.owner,
            invitee=self.invitee, role='viewer',
        )
        self.url = '/api/invites/'

    def test_owner_sees_sent_invite(self):
        c = auth_client(self.owner)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['sent']), 1)

    def test_invitee_sees_received_invite(self):
        c = auth_client(self.invitee)
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['received']), 1)

    def test_unauthenticated_cannot_list_invites(self):
        c = APIClient()
        resp = c.get(self.url)
        self.assertEqual(resp.status_code, 401)


class InviteCancelViewTests(TestCase):

    def setUp(self):
        self.owner = make_user('canown@proj.com', username='canown')
        self.project = make_project(self.owner, 'CanProj')
        self.invitee = make_user('canitee@proj.com', username='canitee')
        self.invite = ProjectInvite.objects.create(
            project=self.project, invited_by=self.owner,
            invitee=self.invitee, role='editor',
        )
        self.url = f'/api/invites/{self.invite.pk}/cancel/'

    def test_sender_can_cancel_invite(self):
        c = auth_client(self.owner)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, 'cancelled')

    def test_cannot_cancel_non_pending_invite(self):
        self.invite.status = 'accepted'
        self.invite.save()
        c = auth_client(self.owner)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_unrelated_user_cannot_cancel(self):
        stranger = make_user('canstr@proj.com')
        c = auth_client(stranger)
        resp = c.post(self.url)
        self.assertEqual(resp.status_code, 403)
