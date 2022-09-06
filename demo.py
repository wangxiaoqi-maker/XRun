import json

#
# d = '{"path":"文件名","data":{"key1":"value1","key2":"value2","key3":"value3"}}'
# data = json.loads(d)
# print(data)
# print(data['data'])


# s = '[{"key":"name","type":"TEXT","value":"wsw"},{"key":"sex","type":"TEXT","value":"nan"}]'
# items = json.loads(s)
# form_data = {}
# for item in items:
#     print(item)
#     if item.get('type') == 'TEXT':
#         form_data[item.get('key')] = item.get('value')
# print(form_data)


data = {"body": 123}
getattr(data, 'body')
