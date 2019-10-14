from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MeiduoPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param ='pagesize'
    # 重写分页的相应体方法
    def get_paginated_response(self, data):
        return Response({
            # 当前总条数
            'counts':self.page.paginator.count,
            # 当前页数据
            'lists':data,
            # 当前页吗
            'page':self.page.number,
            # 总页数"
            'pages':self.page.paginator.num_pages,
            # '每页容量'
            'pagesize':self.page_size
        })