from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings
class FDFSStorage(Storage):
    '''fast_dfs文件储存类'''
    def __init__(self,conf=None, host=None):
        '''初始化 通过参数来方便调整服务器ip和配置文件的位置'''
        if conf is None:
            conf = settings.FDFS_CLIENT_CONF
        self.conf = conf
        if host is None:
            host = settings.FDFS_URL
        self.host = host

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        '''保存文件时使用'''
        # name 选择的上传文件的名字
        # content: 包含上传文件内容的file对象
        # 创建一个Fdfs_client对象
        #
        # upload_by_buffer函数返回的字典内容
        # return dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None
        client = Fdfs_client(self.conf)
        # 上传文件到fdfs中
        res = client.upload_by_buffer(content.read())
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到fdfs失败')

        # 获取返回的文件id
        filename = res.get('Remote file_id')

        return filename




    def url(self,name):
        '''返回访问文件的url路径'''
        return  'http://127.0.0.1:8888/' + name

    def exists(self, name):
        return False