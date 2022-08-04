from rest_framework import serializers


class ProjectSerializers(serializers.Serializer):
    id = serializers.IntegerField(label='项目id', help_text='项目id', required=False, max_value=1000, min_value=3)
    project_name = serializers.CharField(label='项目名称', help_text='项目名称', max_length=20, min_length=3,
                                         error_messages={'min_length': '项目名称不能少于3位',
                                                         'max_length': '项目名称不能超过20位'})
    leader = serializers.CharField(label='项目负责人', help_text='项目负责人', default='王小七')  # leader的默认值为王小七
    is_execute = serializers.BooleanField(label='是否运行', help_text='是否运行')
    desc = serializers.CharField(label='项目简介', help_text='项目简介', allow_null=True)  # desc可以为null
    update_time = serializers.DateTimeField(label='更新时间', help_text='更新时间', format='%Y年%m月%d日 %H:%M:%S', required=False)


class InterfaceSeralizers(serializers.Serializer):
    id = serializers.IntegerField(label='主键id', help_text='主键id', required=False, max_value=1000, min_value=1)
    interface_name = serializers.CharField(label='接口名称', help_text='接口名称', max_length=20, min_length=3)
    tester = serializers.CharField(label='测试人员', help_text='测试人员', max_length=20, min_length=1)
    projects_id = serializers.IntegerField(label='外键项目id', help_text='外键项目id', max_value=1000, min_value=1,
                                           required=False)
    update_time = serializers.DateTimeField(label='更新时间', help_text='更新时间', format='%Y年%m月%d日 %H:%M:%S', required=False)
    # projects = serializers.StringRelatedField(read_only=True)

    projects = ProjectSerializers(read_only=True)

    def create(self, validated_data):
        """
        创建接口数据,手动关联项目表
        :param validated_data:
        :return:
        """
        validated_data['projects'] = validated_data.pop('projects_id')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        更新接口数据,手动关联项目表
        :param instance:
        :param validated_data:
        :return:
        """
        validated_data['projects'] = validated_data.pop('projects_id')
        return super().update(instance, validated_data)
