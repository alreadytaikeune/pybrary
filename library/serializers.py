from django.contrib.auth.models import User

from rest_framework import serializers

from models import Resource, Author, ResourceType, Tag


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ["name"]


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True)
    res_type = serializers.SlugRelatedField(
        queryset=ResourceType.objects.all(), many=False, slug_field="name")
    owner = serializers.SlugRelatedField(
        queryset=User.objects.all(), many=False, slug_field="username")
    tags = TagSerializer(many=True)
    class Meta:
        model = Resource
        fields = '__all__'
