# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import logging



class UserPipeline:
    def process_item(self, item, spider):

        # for user in json.loads(response.body)['res']:
        #     item = BaseUserItem()
        #     for i in list(item.fields.keys()):
        #         if i in user.keys():
        #             item[i] = user[i]
        #         else: item[i] = None
        #     yield item
        # 数据清洗
        # logging.getLogger('UserPipeline').info(item)
        # item['username'] = item['username'].strip()
        # item['email'] = item['email'].strip()

        # 数据验证

        # 保存数据到数据库或其他地方
        return item
