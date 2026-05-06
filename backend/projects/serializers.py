from django.contrib.auth import get_user_model
from rest_framework import serializers
from projects.models import Project, Tag, ProjectMember, ProjectInvite

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ('id', 'name')


class ProjectSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(
            max_length=50,
            error_messages={'max_length': 'Tag nie może być dłuższy niż 50 znaków.'},
        ),
        required=False,
        default=list,
        write_only=True,
    )
    owner   = serializers.StringRelatedField(read_only=True)
    my_role = serializers.SerializerMethodField()

    class Meta:
        model  = Project
        fields = ('id', 'name', 'visibility', 'tags', 'owner', 'my_role', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'my_role', 'created_at', 'updated_at')
        extra_kwargs = {
            'name': {
                'error_messages': {
                    'max_length': 'Nazwa projektu nie może przekraczać 255 znaków.',
                    'blank':      'Nazwa projektu nie może być pusta.',
                    'required':   'Nazwa projektu jest wymagana.',
                }
            }
        }

    def get_my_role(self, instance):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        user = request.user
        if instance.owner == user:
            return 'owner'
        try:
            return instance.members.get(user=user).role
        except ProjectMember.DoesNotExist:
            return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['tags'] = [tag.name for tag in instance.tags.all()]
        return rep

    def _sync_tags(self, project, tag_names):
        tags = []
        for name in tag_names:
            name = name.strip().lower()
            if name:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
        project.tags.set(tags)

    def create(self, validated_data):
        tag_names = validated_data.pop('tags', [])
        project   = Project.objects.create(**validated_data)
        self._sync_tags(project, tag_names)
        return project

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_names is not None:
            self._sync_tags(instance, tag_names)
        return instance


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_id    = serializers.IntegerField(source='user.id', read_only=True)
    user_name  = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model        = ProjectMember
        fields       = ('id', 'user_id', 'user_name', 'user_email', 'role', 'added_at')
        read_only_fields = ('id', 'user_id', 'user_name', 'user_email', 'added_at')


class ProjectInviteSerializer(serializers.ModelSerializer):
    project_id      = serializers.UUIDField(source='project.id', read_only=True)
    project_name    = serializers.CharField(source='project.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.name', read_only=True)
    invitee_id      = serializers.IntegerField(source='invitee.id', read_only=True)
    invitee_name    = serializers.CharField(source='invitee.name', read_only=True)

    class Meta:
        model        = ProjectInvite
        fields       = (
            'id', 'project_id', 'project_name',
            'invited_by_name', 'invitee_id', 'invitee_name',
            'role', 'status', 'created_at', 'responded_at',
        )
        read_only_fields = fields