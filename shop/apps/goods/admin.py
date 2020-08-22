from django.contrib import admin
from django.core.cache import cache
from .models import GoodsType,IndexPromotionBanner,IndexGoodsBanner,IndexTypeGoodsBanner,GoodsSKU,Goods,GoodsImage
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或者更新表中的数据时调用'''
        super().save_model(request, obj, form, change)
        # 发出任务让celery worker 重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 修改内容后要清楚旧的缓存内容
        cache.delete('index_page_data')


    def delete_model(self, request, obj):
        # 删除表中的数据时调用
        super().delete_model(request,obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 修改内容后要清楚旧的缓存内容
        cache.delete('index_page_data')


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class GoodsSKUAdmin(BaseModelAdmin):
    pass


class GoodsAdmin(BaseModelAdmin):
    pass


class GoodsImageAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsImage, GoodsImageAdmin)