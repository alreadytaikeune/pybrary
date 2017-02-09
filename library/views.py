# coding: utf-8
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect

from rest_framework.decorators import api_view, authentication_classes, renderer_classes, parser_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import exceptions
from rest_framework.generics import GenericAPIView, ListAPIView, CreateAPIView
from rest_framework.parsers import BaseParser
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django_filters.rest_framework import DjangoFilterBackend

from utils.authentication import CsrfExemptSessionAuthentication

from serializers import ResourceSerializer, UserSerializer

from models import Resource
from forms import ResourceForm, ResourceTypeForm, OwnerForm

class LoginView(GenericAPIView):
    renderer_classes=(JSONRenderer, TemplateHTMLRenderer)
    template_name = "login.html"

    def process_login(self):
        django_login(self.request, self.user)

    def get_response_serializer(self):
        if getattr(settings, 'REST_USE_JWT', False):
            response_serializer = JWTSerializer
        else:
            response_serializer = TokenSerializer
        return response_serializer

    
    def do_login(self, request, username, password):
        user = auth.authenticate(username=username, password=password)
        if user is None:
            print "auth failed"
            return None
        auth.login(request, user)
        print "user logged in"
        return user


    def get_values(self, qdict):
        next_url = qdict.get('next', "/")
        username = qdict.get('username', None)
        password = qdict.get('password', None)
        return username, password, next_url

    def process(self, request, username, password, next_url):
        user = None
        if username is not None and password is not None:
            user = self.do_login(request, username, password)
        return self.wrap_out(request, user, next_url)

    def get(self, request, *args, **kwargs):
        username, password, next_url = self.get_values(request.GET)
        return self.process(request, username, password, next_url)
        
            
    def post(self, request, *args, **kwargs):
        username, password, next_url = self.get_values(request.POST)
        return self.process(request, username, password, next_url)

    def wrap_out(self, request, user, next_url):
        if user is None:
            return Response(status=401, template_name=self.template_name)
        if next_url is not None:
            redirect(next_url)
        if request.accepted_renderer.format == "html":
            return redirect("/")
        else:
            return Response({'status': 'ok'})


class ResourceListView(ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = ResourceSerializer
    renderer_classes=(JSONRenderer, TemplateHTMLRenderer)
    template_name = "index.html"
    queryset = Resource.objects.all().order_by("added_date")
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('owner', 'res_type')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            for d in data:
                d["authors"] = ", ".join([a["name"] for a in d["authors"]])
            out_data = {}
            out_data["res_types"] = ResourceTypeForm()
            out_data["owners"] = OwnerForm()
            out_data["data"] = data
            return self.get_paginated_response(out_data)

        serializer = self.get_serializer(queryset, many=True)
        # print serializer.data
        data = serializer.data
        for d in data:
            d["authors"] = ", ".join([a["name"] for a in d["authors"]])
        return Response({"results": serializer.data})


class SignupView(GenericAPIView):
    renderer_classes=(JSONRenderer, TemplateHTMLRenderer)
    template_name = "signup.html"
    serializer_class = UserSerializer

    def get(self, request):
        return Response()

    def post(self, request, *args, **kwargs):
        ser = UserSerializer(data=request.POST)
        if ser.is_valid():
            user = ser.save()
            auth.login(request, user)
            if request.accepted_renderer.format == "html":
                return redirect("/")
            else:
                return Response(ser.data)
        return Response(ser.errors)


@api_view(['GET'])
@renderer_classes((JSONRenderer, TemplateHTMLRenderer))
def logout(request):
    auth.logout(request)
    if request.accepted_renderer.format == "html":
        return Response(template_name="login.html")
    else:
        return Response("logged out")



def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


class PDFParser(BaseParser):
    """
    Plain text parser.
    """
    media_type = 'multipart/form-data'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        return stream.read()

# @api_view(['POST'])
# @renderer_classes((JSONRenderer,))
# @authentication_classes((CsrfExemptSessionAuthentication, BasicAuthentication))
# @parser_classes((PDFParser,))
@login_required()
@csrf_exempt
def upload_res(request):
    # print request.POST.title()
    # print request.FILES

    print request.FILES
    print request.POST
    form = ResourceForm(request.POST, request.FILES)
    form.set_request(request)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(instance)
    else:
        print 'not valid'
        print form.errors
        return HttpResponseBadRequest(form.errors, content_type='application/json')


class ResourceView(mixins.RetrieveModelMixin, GenericAPIView):
    renderer_classes=(JSONRenderer, TemplateHTMLRenderer)
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    template_name = "resource.html"

    def get(self, request, *args, **kwargs):
        if not "pk" in kwargs:
            return Response(status=400)
        data = self.serializer_class(Resource.objects.get(pk=kwargs["pk"])).data
        return Response({"data": data})
