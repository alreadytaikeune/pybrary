# coding: utf-8
from __future__ import unicode_literals
from django.db import models
from datetime import datetime    
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.db import models

from utils import slug

# Create your models here.


class Author(models.Model):
    class Meta:
        db_table = "author"
    name = models.CharField(verbose_name=_('name'),max_length=200, default='')
    slug_name = models.CharField(verbose_name=_('slug name'), max_length=200, 
        default='', unique=True)
    added_date = models.DateTimeField(_('date added to the database'),auto_now_add=True)
    updated_date = models.DateTimeField(_('date updated to the database'),auto_now=True)

    def __unicode__(self):
        return self.name 

    class Meta:
        verbose_name = _("author")
        verbose_name_plural = _("authors")
        default_permissions = []
    ordering = ['name', 'added_date']


class ResourceType(models.Model):
    class Meta:
        db_table = "resource_type"
    name = models.CharField(verbose_name=_('name'), max_length=200)
    slug_name = models.CharField(verbose_name=_('slug name'), max_length=200,
        default="")
    
    def save(self, **kwargs):
        self.slug_name = slug(self.name)
        super(ResourceType, self).save(**kwargs)

    def __unicode__(self):
        return self.name

class Tag(models.Model):
    class Meta:
        db_table = "tag"
    name = models.CharField(verbose_name=_('tag name'), max_length=200, unique=True)

    slug_name = models.CharField(verbose_name=_('slug_name'), max_length=200, unique=True,
        null=True, blank=True, default="")

    def save(self, **kwargs):
        self.slug_name = slug(self.name)
        super(Tag, self).save(**kwargs)
    
    def __unicode__(self):
        return "#" + self.name

class Resource(models.Model):

    title = models.CharField(verbose_name=_('title'),max_length=200, unique=True)
    added_date = models.DateTimeField(_('date added to the library'),auto_now_add=True)
    updated_date = models.DateTimeField(_('date updated to the database'),auto_now=True)
    authors = models.ManyToManyField(Author,verbose_name=_('author'))
    summary = models.TextField(verbose_name=_('summary'),blank=True,default="")
    res_type = models.ForeignKey(ResourceType, null=False, default=1, verbose_name=_('resource type'))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'))
    owner = models.ForeignKey(User,blank=True,verbose_name=_('owner'), default=1)
    document = models.FileField(upload_to="docs", max_length=512, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _("resource")
        verbose_name_plural = _("resources")
        default_permissions = []
        ordering = ['title']
