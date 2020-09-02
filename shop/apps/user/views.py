from goods.models import GoodsSKU
from django.shortcuts import render, redirect,reverse
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from order.models import OrderInfo, OrderGoods
from user.models import User, Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired # 导入解密超时的异常
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection

import re
# Create your views here.


# /user/register
# def register(request):
#     '''用户的注册处理'''
#     if request == 'GET':
#         # 如果是GET请求显示注册页面
#         return render(request,'register.html')
#
#     else:
#         # 如果是POST请求
#         '''对注册页面提交的信息进行处理'''
#         # 接收数据
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         # 对数据进行校验
#         if not all([username, password, email]):
#             return render(request, 'register.html', {'errmsg': '请填写所有的信息'})
#         # 校验邮箱
#         if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': '请填写正确的邮箱信息'})
#         # 处理协议的勾选
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '请确认并勾选服务协议'})
#         # 校验用户名是否存在
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             # 用户不存在
#             user = None
#
#         if user:
#             return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
#         # 业务处理:注册用户
#         # 使用django用户类自带的create_user()来进行注册
#         user = User.objects.create_user(username, email, password)
#
#         # 返回应答,跳转到首页
#         return redirect(reverse('goods:index'))

# 使用类视图（CBV）
class RegisterView(View):
    '''注册用类视图'''
    def get(self,request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''处理注册请求'''
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 对数据进行校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '请填写所有的信息'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '请填写正确的邮箱信息'})
        # 处理协议的勾选
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请确认并勾选服务协议'})
        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户不存在
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 业务处理:注册用户
        # 使用django用户类自带的create_user()来进行注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 发送激活邮件， 包含激活链接  user/active/
        # 激活链接中需要包含用户的身份信息 并且对身份信息进行加密\
        # 加密用户的身份信息 生成激活的token
        # 可以使用django自带的secretkey作为秘钥
        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()  # serializer.dumps()返回的数据类型是byte型的，要通过decode()来转化成utf-8字符串
        # 发邮件(该函数功能已经转移到task.py 中做异步处理)
        # subject = '天天生鲜欢迎信息'  # 邮件的主题
        # message = ''
        # sender = settings.EMAIL_FROM  # 发件人
        # html_message =  '<h1>%s, 欢迎您成为天天生鲜的注册会员</h1>，请点击下方的链接来激活您的账户<br><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'  %(username, token, token) # 邮件的正文
        # receiver = [email] # 收件人列表
        # send_mail(subject, message, sender, receiver,html_message=html_message)
        # 返回应答,跳转到首页
        ## 使用celery发送邮件
        send_register_active_email.delay(email,username,token)
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        # 解密 获取用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取用户id
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
        # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# user/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'

        else:
            username = ''
            checked = ''
        # 使用模板
        '''显示登录页面'''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):

        '''用户登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整，请填写所有字段'})

        # 登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名和密码正确 判断用户是否激活
            if user.is_active:
                # 用户已激活 登录正常 记录用户状态
                login(request, user)
                # 获取登录后要跳转的页面
                # 如果有next返回获取的结果，如果没有就跳转到指定的页面
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到next页面

                # 判断是否记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    response = redirect(next_url)
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response = redirect(next_url)
                    response.delete_cookie('username', username)
                # 跳转到首页
                return response

            else:
                return render(request, 'login.html', {'errmsg':'账户未激活'})

        else:
            # 用户名或者密码错误
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


# /user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self,request):
        '''用户登出'''
        # 清除用户的登录信息session
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))

# /user
class UserInfoView(LoginRequiredMixin,View):
    '''用户信息页面'''
    def get(self, request):
        '''显示'''
        # page = user
        # request.user
        # 如果用户没有登录，request.user 会是一个AnnoymouseUser实例
        # 如果用户已经登录，则是一个User类 的实例
        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户的历史浏览记录
        con = get_redis_connection('default')
        history_key = 'history_%d' %user.id
        # 获取用户最新浏览的五条浏览记录
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        # 通过遍历来获取商品的信息
        goods_li = []
        for id in sku_ids:
            try:
                goods = GoodsSKU.objects.get(id=id)
            except GoodsSKU.DoesNotExist:
                pass
            goods_li.append(goods)

        # 组织上下文
        context = {
            'page': 'page',
            'address': address,
            'goods_li':goods_li
        }

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 5)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page':order_page,
                   'pages':pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)

# /user/address
class AdsdressView(LoginRequiredMixin,View):
    '''用户地址页面'''
    def get(self, request):
        '''显示'''
        # page = address
        # 获取用用户的User对象
        user = request.user
        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        #
        #     # 不存在默认的收货地址
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address','address':address})

    def post(self,request):

        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})
        # 校验手机号
        if not re.match(r'^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$',phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机格式不正确'})

        # 业务处理，添加地址
        # 如果用户已存在默认地址，则添加的地址不作为默认地址，否则作为默认地址来添加
        # 获取登录用户的user对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认的收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答　刷新地址页面
        return redirect(reverse('user:address'))