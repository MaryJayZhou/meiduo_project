from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAdminUser

from apps.users.models import User
from apps.meiduo_admin.serializers.users import UserSerializer
from rest_framework.pagination import PageNumberPagination
from apps.meiduo_admin.utils.pagination import MeiduoPagination

class UserView(ListCreateAPIView):

    # permission_classes = [IsAdminUser]
    # queryset = User.objects.filter(is_staff=False)

    def get_queryset(self):
        # 获取搜索关键字
        keyword = self.request.query_params.get('keyword')
        # 在用户名上进行关键字查询
        return User.objects.filter(is_staff=False,username__contains = keyword)

    serializer_class = UserSerializer

    # 分页
    pagination_class = MeiduoPagination
