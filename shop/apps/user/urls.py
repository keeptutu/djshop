from django.urls import path
from user import views
from .views import RegisterView,ActiveView,LoginView,LogoutView
from .views import UserInfoView, UserOrderView, AdsdressView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    # path('register/', views.register, name='register'),  # 注册
    path('register/', RegisterView.as_view(), name='register'),
    path('active/<str:token>', ActiveView.as_view(), name='active'),  # 用户激活
    path('login/', LoginView.as_view(), name='login'),  # 用户登录
    path('logout/', LogoutView.as_view(), name='logout'), # 用户登出
  # path('', login_required(UserInfoView.as_view()), name='user'),  # 用户中心页面
  # path('order/', login_required(UserOrderView.as_view()), name='order'),  # 用户订单页面
#   path('address/', login_required(AdsdressView.as_view()), name='address')  # 用户地址页面
    path('', UserInfoView.as_view(), name='user'), # 以下三个都是用户信息页面
    path('order/', UserOrderView.as_view(), name='order'),
    path('address/', AdsdressView.as_view(), name='address'),

 ]
