# 导入所需的包
import json
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# 声明基类
Base = declarative_base()


# 定义UserSelector类，代表数据库表
class UserSelector(Base):
    __tablename__ = 'company'

    #
    company = Column(String(50), primary_key=True)
    website = Column(String(255), default=None)
    remove_dialog_selector = Column(String(255), default=None)
    remove_other_selector = Column(String(255), default=None)
    page_finished_selector = Column(String(255), default=None)
    user_card_selector = Column(String(255), default=None)
    user_audio_selector = Column(String(255), default=None)

    # 个人信息
    Name_selector = Column(String(255), default=None)
    Age_selector = Column(String(500), default=None)
    SexBg_selector = Column(String(255), default=None)
    SexImg_selector = Column(String(255), default=None)
    Online_selector = Column(String(255), default=None)
    Position_selector = Column(String(500), default=None)
    Grade_selector = Column(String(255), default=None)
    GradePrice_selector = Column(String(255), default=None)
    GradeImg_selector = Column(String(255), default=None)
    Service_selector = Column(String(255), default=None)
    ServiceSep_selector = Column(String(255), default=None)
    Tag_selector = Column(String(255), default=None)
    TagSep_selector = Column(String(255), default=None)
    AvatarImg_selector = Column(String(255), default=None)
    Profile_selector = Column(String(255), default=None)


# 将JSON数据转换为数据库表
def json_to_database():
    # 读取JSON文件
    with open('/Users/colin/Library/Mobile Documents/com~apple~CloudDocs/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider/data/user_selector.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 创建数据库连接
    engine = create_engine('mysql+mysqlconnector://colin:^Q}spft2L0bmX^+=X=v0@140.250.51.124/duopei?charset=utf8mb4')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建表结构
    UserSelector.__table__.create(bind=engine, checkfirst=True)

    # 创建数据库会话
    session = SessionLocal()

    try:
        for key, value in data.items():
            print(key)
            user_selector = UserSelector(
                    company=value['company'],
                    website=key,
                    remove_other_selector=value['remove_other_selector'],
                    remove_dialog_selector=value['remove_dialog_selector'],
                    user_card_selector=value['user_card_selector'],
                    page_finished_selector=value['page_finished_selector'],
                    user_audio_selector=value['user_audio_selector'],
                    # 其他字段...
                    Name_selector=value['user_info_selector']['Name'] if 'Name' in value['user_info_selector'] else None,
                    Age_selector=value['user_info_selector']['Age'] if 'Age' in value['user_info_selector'] else None,
                    SexBg_selector=value['user_info_selector']['SexBg'] if 'SexBg' in value['user_info_selector'] else None,
                    SexImg_selector=value['user_info_selector']['SexImg'] if 'SexImg' in value['user_info_selector'] else None,
                    Online_selector=value['user_info_selector']['Online'] if 'Online' in value['user_info_selector'] else None,
                    Position_selector=value['user_info_selector']['Position'] if 'Position' in value['user_info_selector'] else None,
                    Grade_selector=value['user_info_selector']['Grade'] if 'Grade' in value['user_info_selector'] else None,
                    GradePrice_selector=value['user_info_selector']['GradePrice'] if 'GradePrice' in value['user_info_selector'] else None,
                    GradeImg_selector=value['user_info_selector']['GradeImg'] if 'GradeImg' in value['user_info_selector'] else None,
                    Service_selector=value['user_info_selector']['Service'] if 'Service' in value['user_info_selector'] else None,
                    ServiceSep_selector=value['user_info_selector']['ServiceSep'] if 'ServiceSep' in value['user_info_selector'] else None,
                    Tag_selector=value['user_info_selector']['Tag'] if 'Tag' in value['user_info_selector'] else None,
                    TagSep_selector=value['user_info_selector']['TagSep'] if 'TagSep' in value['user_info_selector'] else None,
                    AvatarImg_selector=value['user_info_selector']['AvatarImg'] if 'AvatarImg' in value['user_info_selector'] else None,
                    Profile_selector=value['user_info_selector']['Profile'] if 'Profile' in value['user_info_selector'] else None,

            )
            session.merge(user_selector)
        session.commit()
    except Exception as e:
        session.rollback()
        print(e)
    finally:
        session.close()


# 调用函数
json_to_database()
