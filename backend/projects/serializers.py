from rest_framework import serializers
from projects.models import Project, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ('id', 'name')


class ProjectSerializer(serializers.ModelSerializer):
    # Tagi przyjmujemy jako listę stringów (nazw), zwracamy tak samo
    tags  = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        write_only=True,
    )
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = Project
        fields = ('id', 'name', 'visibility', 'tags', 'owner', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """Przy odczycie zamieniamy obiekty Tag → same nazwy (stringi)."""
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