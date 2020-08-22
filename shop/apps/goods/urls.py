from django.urls import path
from .views import IndexView, DetailView
urlpatterns = [
    path('index/', IndexView.as_view(), name='index'),  # 首页
    path('goods/<int:goods_id>', DetailView.as_view(), name='detail')  # 商品详情页
]
