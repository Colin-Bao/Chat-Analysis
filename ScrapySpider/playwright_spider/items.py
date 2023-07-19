# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class UserItem(Item):
    """
    基础用户信息：在首页能获取到的一级信息
    """
    rank = Field()
    rank_2 = Field()
    website = Field()
    homepage = Field()
    crawl_date = Field()
    crawl_date_2 = Field()
    audio_url = Field()
    Name = Field()
    Age = Field()
    SexBg = Field()
    SexImg = Field()
    Online = Field()
    Position = Field()
    Grade = Field()
    GradePrice = Field()
    GradeImg = Field()
    Service = Field()
    Tag = Field()
    Tag2 = Field()
    AvatarImg = Field()
    Profile = Field()
    company = Field()
