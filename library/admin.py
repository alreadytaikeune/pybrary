from django.contrib import admin
from library.models import Author, Resource, ResourceType, Tag
# Register your models here.

admin.site.register(Author)
admin.site.register(Resource)
admin.site.register(ResourceType)
admin.site.register(Tag)