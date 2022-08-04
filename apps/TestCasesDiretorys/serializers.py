from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from TestCasesDiretorys.models import TestcaseDirectory


class TestCaseDirectorySerializer(serializers.ModelSerializer):
    # parent_directory = serializers.PrimaryKeyRelatedField(label='父目录', help_text='父目录',
    #                                                       queryset=TestcaseDirectory.objects.all())

    class Meta:
        model = TestcaseDirectory
        fields = ('id', 'name', 'projects', 'parent')
        extra_kwargs = {
            'parent': {'required': False}}

    def create(self, validated_data):
        """
        不同项目下可以创建相同目录名称
        同项目下不同目录级别可以创建相同目录名称
        :param validated_data:
        :return:
        """
        duplicate_name = TestcaseDirectory.objects.filter(name=validated_data['name'],
                                                          projects=validated_data['projects'],
                                                          parent_id=validated_data.get('parent'))
        if duplicate_name:
            # 判断是否是同一个目录
            raise serializers.ValidationError({"code": "400", "msg": "目录名称已存在", "success": False})
        validated_data['create_user'] = self.context['request'].user
        return super().create(validated_data)
