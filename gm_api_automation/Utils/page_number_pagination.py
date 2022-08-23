from rest_framework.pagination import PageNumberPagination as _PageNumberPagination


class PageNumberPagination(_PageNumberPagination):
    # 指定默认每一页显示3条数据
    page_size = 1000

    # 前端用于指定页码的查询字符串参数名称
    page_query_param = 'pageNo'
    # 前端用于指定页码的查询字符串参数描述
    page_query_description = '获取的页码'

    # 前端用于指定每一页显示的数据条数，查询字符串参数名称
    page_size_query_param = 'pageSize'
    page_size_query_description = '每一页数据条数'

    max_page_size = 1000

    invalid_page_message = '无效页码'

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['current_num'] = self.page.number
        response.data['max_num'] = self.page.paginator.num_pages
        response.data['total'] = response.data['count']
        del response.data['count']
        return response