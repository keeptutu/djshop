from django.urls import path
from .views import OrderPlaceView, OrderCommitView, OrderPayView, CheckView
urlpatterns = [
    path('place/', OrderPlaceView.as_view(), name='place'),  # 订单的展示
    path('commit/', OrderCommitView.as_view(), name='commit'),  # 订单的创建
    path('pay/', OrderPayView.as_view(), name='pay'),  # 支付
    path('check/', CheckView.as_view(), name='check'),  # 确认支付结果

]
