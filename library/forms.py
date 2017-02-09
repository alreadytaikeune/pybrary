# coding: utf-8
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from utils import slug

from models import Resource, Tag, Author, ResourceType


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ('title', 'document', 'authors', 'tags', 'res_type',
            'summary')

    # def __init__(self, request, *args, **kwargs):
    #     super(ResourceForm, self).__init__(self, *args, **kwargs)
    #     self._request = request

    def set_request(self, request):
        self._request = request

    def get_or_create_from_name(self, entities_name, entity_class):
        print entities_name
        out = []
        slug_entities = [slug(n) for n in entities_name]
        nb_created = 0
        for i, se in enumerate(slug_entities):
            entity, created = entity_class.objects.get_or_create(slug_name=se, 
                    defaults={'name': entities_name[i]})
            if created:
                nb_created += 1
            out.append(entity.pk)

        print "{} {} created".format(nb_created, entity_class.__name__)
        return out

    def is_valid(self):
        print "self data is"
        print self.data
        data = {}
        self.make_authors(data)
        self.make_tags(data)
        self.make_res_type(data)
        if "title" in self.data:
            data["title"] = self.data["title"]
        self.data = data
        print "Formatted data is"
        print self.data
        return super(ResourceForm, self).is_valid()

    def make_authors(self, data):
        print "clean authors"
        if not 'authors' in self.data:
            return
        names = self.data.getlist("authors")
        authors = self.get_or_create_from_name(names, Author)
        data["authors"] = authors

    def make_tags(self, data):
        print "clean tags"
        if not 'tags' in self.data:
            return
        names = self.data.getlist("tags")
        data["tags"] = self.get_or_create_from_name(names, Tag)


    def make_res_type(self, data):
        print "clean res type"
        if not 'res_type' in self.data:
            return
        name = self.data["res_type"]
        data["res_type"] = ResourceType.objects.get_or_create(
            slug_name=slug(name), defaults={'name':name})[0].pk

    def clean_document(self):
        print "clean document"
        document = self.cleaned_data['document']
        content_type = document.content_type
        print content_type
        # if content_type in settings.CONTENT_TYPES:
        if document._size > settings.MAX_FILE_SIZE:
            raise forms.ValidationError(_('Please keep filesize under {}. Current filesize {}').format(
                settings.MAX_FILE_SIZE, document._size))
        return document

    def save(self, commit=True):
        print "saving"
        instance = forms.ModelForm.save(self, False)
        instance.onwer = self._request.user
        # Prepare a 'save_m2m' method for the form,
        old_save_m2m = self.save_m2m
        def save_m2m():
           old_save_m2m()
           instance.tags.clear()
           for tag in self.cleaned_data['tags']:
               instance.tags.add(tag)
        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class ResourceTypeForm(forms.Form):
    res_types = forms.ModelChoiceField(queryset=ResourceType.objects.all().order_by('name'))


class OwnerForm(forms.Form):
    owners = forms.ModelChoiceField(queryset=User.objects.all().order_by('username'))