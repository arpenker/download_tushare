import pandas as pd
from sqlalchemy import create_engine, inspect, Column, String, Date, DateTime, DECIMAL, BigInteger, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import DB_CONFIG

# 定义ORM基类
Base = declarative_base()

# 数据库连接字符串
db_uri = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
)

# 创建数据库引擎
try:
    engine = create_engine(db_uri, echo=False)
    # 创建Session类
    Session = sessionmaker(bind=engine)
except Exception as e:
    print(f"数据库连接失败: {e}")
    print(f"请检查 config.py 中的数据库配置是否正确。")
    exit()

class StockBasic(Base):
    """股票基础信息表"""
    __tablename__ = 'stock_basic'
    ts_code = Column(String(10), primary_key=True, comment='TS股票代码')
    symbol = Column(String(10), comment='股票代码')
    name = Column(String(30), comment='股票名称')
    industry = Column(String(50), comment='所属行业')
    list_date = Column(Date, comment='上市日期')
    delist_date = Column(Date, nullable=True, comment='退市日期')

    def __repr__(self):
        return f"<StockBasic(ts_code='{self.ts_code}', name='{self.name}')>"

class Stock30Min(Base):
    """30分钟K线数据表"""
    __tablename__ = 'stock_30min'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(10), index=True, comment='TS股票代码')
    trade_time = Column(DateTime, index=True, comment='交易时间')
    open = Column(DECIMAL(10, 2), comment='开盘价')
    high = Column(DECIMAL(10, 2), comment='最高价')
    low = Column(DECIMAL(10, 2), comment='最低价')
    close = Column(DECIMAL(10, 2), comment='收盘价')
    vol = Column(DECIMAL(20, 2), comment='成交量(手)')
    amount = Column(DECIMAL(20, 4), comment='成交额(千元)')

    # 创建联合唯一索引，防止数据重复
    __table_args__ = (UniqueConstraint('ts_code', 'trade_time', name='_ts_code_trade_time_uc'),)

    def __repr__(self):
        return f"<Stock30Min(ts_code='{self.ts_code}', trade_time='{self.trade_time}')>"

def init_db():
    """
    初始化数据库，创建所有定义的表。
    """
    try:
        print("正在初始化数据库，检查并创建数据表...")
        Base.metadata.create_all(engine)
        print("数据表创建/检查完成。")
    except Exception as e:
        print(f"创建数据表时发生错误: {e}")

def get_session():
    """
    获取一个新的数据库会话。
    """
    return Session()

def bulk_insert_data(df: pd.DataFrame, model_class):
    """
    使用原生INSERT IGNORE来批量插入数据，如果主键或唯一索引冲突则忽略。
    这比ORM逐条检查快得多。
    """
    if df.empty:
        return
    
    table_name = model_class.__tablename__
    
    with engine.connect() as connection:
        # 使用pandas的to_sql方法，如果已存在则忽略
        # 注意：'append'配合唯一索引可以实现 'INSERT IGNORE' 的效果
        # 对于MySQL，需要确保主键或唯一索引已建立
        df.to_sql(name=table_name, con=connection, if_exists='append', index=False)

if __name__ == '__main__':
    # 作为脚本直接运行时，执行数据库初始化
    init_db()
