from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from Executed.serializers import SendHttpRequestSeralizer
from gm_api_automation.middleware.HttpClient import Request


class SendHttpRequestView(ModelViewSet):
    queryset = None
    serializer_class = SendHttpRequestSeralizer
    permission_classes = [IsAuthenticated]

    def run_http_request(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = request.data.get('address')
        method = request.data.get('method')
        bodys = request.data.get('body')
        headers = request.data.get('headers')
        body_type = request.data.get('body_type')
        data = Request(url, body=bodys).request(method=method, body_type=body_type, headers=headers)
        return Response(data)
