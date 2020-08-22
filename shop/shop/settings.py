"""
Django settings for shop project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import sys
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
# 当不想在设置中使用app.xxx的时候可以启用上一行的设置来添加文件的搜索路径

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'jp2fp^to_n-6!7+^wong=w4r3r&sf$+l(tn_=c(%2y3f#s5jes'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user',  # 用户模块
    'cart',  # 商品模块
    'order',  # 购物车模块
    'goods',  # 订单模块
    'tinymce',  # 富文本编辑器
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # 添加模板文件夹的路径
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'shop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# 使用mysql作为项目的数据库支持 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'USER': 'root',
        'PASSWORD': '164441960',
        'HOST': '47.102.149.118',
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'  # 更改中文配置

TIME_ZONE = 'Asia/Shanghai'  # 更改时区的设置

USE_I18N = True

USE_L10N = True

USE_TZ = True

CELERY_TIMEZONE = 'Asia/Shanghai'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 富文本编辑器的配置信息
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',  # 主题的选择
    'width': 600,  # 宽度
    'height': 400,  # 高度
}
# 设置使用django的模型类
AUTH_USER_MODEL = 'user.User'

# 邮箱SMTP的相关设置

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = '465'
# 465端口需要进行ssl加密验证
EMAIL_USE_SSL = True
# 发送邮件的邮箱
EMAIL_HOST_USER = 'SHOWMYTEST@163.com'
# 邮箱中设置的授权密码
EMAIL_HOST_PASSWORD = 'UOYKKXZLJLWMQWZL'
# 收件人看到的发件人信息
EMAIL_FROM = EMAIL_HOST_USER

# django的缓存配置
#使用redis来保存session
#使用的工具是django-redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # redis的缓存地址
        "LOCATION": "redis://47.102.149.118/9",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
}

}
# 配置session的存储
# 使用redis来进行缓存
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


# 配置登录的url地址
LOGIN_URL = '/user/login'

# 改变文件上传的配置文件
DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FDFSStorage'

# FDFS配置 设置fastdfs的client.conf配置文件路径
FDFS_CLIENT_CONF = './utils/fdfs/client.conf'
# FDFS存储服务器上nginx的ip和端口号
FDFS_URL = '127.0.0.1/8888'
