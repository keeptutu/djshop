from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from django.db import transaction
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
from datetime import datetime
from alipay import AliPay
from django.conf import settings
import os

# Create your views here.

# /order/place/
class OrderPlaceView(LoginRequiredMixin, View):
    '''订单提交页面'''
    def post(self,request):
        '''提交订单页面'''
        # 获取的登录的用户
        user = request.user
        # 获取参数sku_ids
        sku_ids = request.POST.getlist('sku_ids')
        # 校验参数
        if not sku_ids:
            # 跳转到购物车的页面
            return redirect(reverse('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' %user.id

        skus = []
        total_count = 0  # 商品的总数量
        total_price = 0  # 商品的总价格
        # 遍历sku_ids来获取用户要购买的商品信息
        for sku_id in sku_ids:

            # 通过sku_id来获得商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性 保存商品的数量和小计
            sku.count = int(count)
            sku.amount = amount
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount

        # 运费的计算 根据实际情况来进行计算
        # 设置固定的10元运费
        transit_price = 10

        # 需要支付的金额
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文

        sku_ids = ','.join(sku_ids)
        context = {
            'skus':skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
        }


        # 渲染模板
        return render(request, 'place_order.html', context=context)

# 前端传递的参数
# 地址id(addr_id) 支付方式(pay_method) 用户要购买的商品id字符串(sku_ids)
class OrderCommitView(View):
    '''创建订单'''
    @transaction.atomic
    def post(self, request):
        '''订单创建'''
        # 判断用户是否已经登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

         # 获取参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res':2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址不存在'})

        # 创建事务保存点
        save_id = transaction.savepoint()

        try:
            # todo:创建订单的核心业务
            # 补充和组织缺少的参数
            # 　订单id  时间精确到秒 + 用户的id
            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
            # 运费
            transit_price = 10
            # 总数目和总金额 先设置默认值
            total_count = 0
            total_price = 0

            # todo:向df_order_info 表中增加一个记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price,
                                             )

            # todo:用户订单中有几个商品就要向df_order_goods表中添加几个记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            # 通过sku_ids 来获取商品的信息
            sku_ids = sku_ids.split(',')  # 将字符串变成了列表

            for sku_id in sku_ids:
                # 通过sku_id 来获取商品的信息
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    # 回滚点保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                # 从redis中获取用户要购买的商品数目
                count = conn.hget(cart_key, sku_id)

                # todo:确认商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # todo:向df_order_goods中添加一条记录
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # todo:更新商品的库存和销量信息
                sku.stock -= int(count)
                sku.sales -= int(count)
                sku.save()

                # todo 累加计算订单中商品的总件数和总价格
                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

                # todo:更新订单信息表中的商品总数量和总价格
                order.total_count = total_count
                order.total_price = total_price
                order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # todo: 提交事务
        transaction.savepoint_commit(save_id)


        # todo: 清除用户购物车中的记录

        conn.hdel(cart_key, *sku_ids)

                # 返回订单

        return JsonResponse({'res': 5, 'errmsg': '创建成功'})


# order/pay
class OrderPayView(View):
    '''订单的支付'''
    def post(self, request):
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理 使用python sdk调用支付宝的接口
        # 初始化
        pravite_key = open(os.path.join(settings.BASE_DIR, 'apps/order/app_pravite_key.pem')).read()
        public_key = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()


        alipay = AliPay(
            appid='2021000118642449',
            app_notify_url=None,
            app_private_key_string=pravite_key,
            alipay_public_key_string=public_key,
            sign_type='RSA2',
            debug=True,
        )

        # 调用支付接口
        total_pay = order.total_price + order.transit_price  #decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付金额
            subject='天天生鲜%s' %order_id,
            return_url=None,
            notify_url=None,
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# ajax post
# 前端传递的参数 订单id(order_id)
# /order/check/
class CheckView(View):
    '''查看订单的支付结果'''
    def post(self, request):
        '''查询支付结果'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理 使用python sdk调用支付宝的接口
        # 业务处理 使用python sdk调用支付宝的接口
        # 初始化
        pravite_key = open(os.path.join(settings.BASE_DIR, 'apps/order/app_pravite_key.pem')).read()
        public_key = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()


        alipay = AliPay(
            appid='2021000118642449',
            app_notify_url=None,
            app_private_key_string=pravite_key,
            alipay_public_key_string=public_key,
            sign_type='RSA2',
            debug=True,
        )

        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            '''返回的字典的格式
            response = {
                "alipay_trade_query_response": {
                    "trade_no": "2017032121001004070200176844",
                    "code": "10000",
                    "invoice_amount": "20.00",
                    "open_id": "20880072506750308812798160715407",
                    "fund_bill_list": [
                        {
                            "amount": "20.00",
                            "fund_channel": "ALIPAYACCOUNT"
                        }
                    ],
                    "buyer_logon_id": "csq***@sandbox.com",
                    "send_pay_date": "2017-03-21 13:29:17",
                    "receipt_amount": "20.00",
                    "out_trade_no": "out_trade_no15",
                    "buyer_pay_amount": "20.00",
                    "buyer_user_id": "2088102169481075",
                    "msg": "Success",
                    "point_amount": "0.00",
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "20.00"
                }
                '''
            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝的交易号
                trade_no = response.get('trade_no')
                # 更新订单的状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回应答
                return JsonResponse({'res': 3, 'errmsg': '支付成功'})
            elif code == '10000' or code == '40004' and response.get('trade_status') == 'WAIT_BUYER_PAY':
                # 等待买家付款
                import time
                time.sleep(5)
                continue

            else:
                # 支付出错
                # 返回对应的错误信息
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})