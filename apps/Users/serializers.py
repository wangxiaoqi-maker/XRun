from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler


class RegisterModel(serializers.ModelSerializer):
    password_confirm = serializers.CharField(label='确认密码', help_text='确认密码', max_length=21, min_length=6,
                                             write_only=True,
                                             error_messages={"min_length": "密码长度不能小于6位", "max_length": "密码长度不能大于21位"})
    token = serializers.CharField(label='token', help_text='token', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'token', 'username', 'password_confirm', 'password', 'email')
        extra_kwargs = {
            'email': {
                'required': False,  # 必须
                # 'error_messages': {'required': '邮箱不能为空'},
                # 'write_only': True,
                # 'validators': [UniqueValidator(queryset=User.objects.all(), message='邮箱已存在')]
            },
            'password': {
                'write_only': True
            }
        }

    def validate(self, attrs):
        if attrs['password'] == attrs['password_confirm']:
            attrs.pop('password_confirm')
            return attrs
        else:
            raise serializers.ValidationError('两次密码不一致')

    def create(self, validated_data):
        # user = User.objects.create_user(username=validated_data['username'], email=validated_data['email'],
        #                                 password=validated_data['password'])
        user = User.objects.create_user(**validated_data)
        payload = jwt_payload_handler(user)
        user.token = "Bearer " + jwt_encode_handler(payload)
        return user
