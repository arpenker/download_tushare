import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func
from tqdm import tqdm

from . import config
from . import database as db

# ------------------ Tushare API Initialization ------------------
try:
    ts.set_token(config.TUSHARE_TOKEN)
    pro = ts.pro_api()
    print("Tushare API 初始化成功。")
except Exception as e:
    print(f"Tushare API 初始化失败: {e}")
    print("请检查 config.py 中的 TUSHARE_TOKEN 是否正确。")
    exit()

def update_stock_basic():
    """
    更新本地的股票基础信息表。
    """
    print("正在更新股票基础信息...")
    try:
        # 获取所有A股列表
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,list_date')
        
        # 对'industry'列的None值进行处理，替换为空字符串或其他默认值
        data['industry'] = data['industry'].fillna('')

        # 使用我们封装的批量插入函数
        db.bulk_insert_data(data, db.StockBasic)
        print(f"股票基础信息更新完成，共获取 {len(data)} 条数据。")
    except Exception as e:
        print(f"更新股票基础信息时发生错误: {e}")

def get_stock_list():
    """从数据库获取所有需要同步的股票列表"""
    session = db.get_session()
    # 选择所有未退市的股票
    stocks = session.query(db.StockBasic).filter(db.StockBasic.delist_date == None).all()
    session.close()
    return stocks

def full_sync():
    """
    全量同步所有A股的30分钟K线数据。
    这是一个耗时操作。
    """
    print("开始全量同步30分钟K线数据，这将是一个非常耗时的操作。")
    update_stock_basic()  # 首先确保股票列表是最新的
    stocks_to_sync = get_stock_list()

    with tqdm(total=len(stocks_to_sync), desc="全量同步进度") as pbar:
        for stock in stocks_to_sync:
            pbar.set_description(f"正在同步 {stock.ts_code}")
            _sync_stock_data(stock.ts_code, start_date=config.START_DATE or stock.list_date.strftime('%Y%m%d'))
            pbar.update(1)
    print("所有股票全量同步完成。")

def update_sync():
    """
    增量同步所有A股的30分钟K线数据。
    """
    print("开始增量同步30分钟K线数据...")
    update_stock_basic()
    stocks_to_sync = get_stock_list()
    
    session = db.get_session()
    
    # --- 性能优化：一次性查询所有股票的最新时间 ---
    print("正在查询所有股票的最新记录时间...")
    latest_records_query = session.query(
        db.Stock30Min.ts_code,
        func.max(db.Stock30Min.trade_time)
    ).group_by(db.Stock30Min.ts_code).all()

    # 将查询结果转为字典以便快速查找: {'ts_code': latest_time}
    latest_records_map = {ts_code: max_time for ts_code, max_time in latest_records_query}
    print("查询完成。")
    # -------------------------------------------

    with tqdm(total=len(stocks_to_sync), desc="增量同步进度") as pbar:
        for stock in stocks_to_sync:
            pbar.set_description(f"增量同步 {stock.ts_code}")
            
            latest_record = latest_records_map.get(stock.ts_code)
            
            if latest_record:
                # 从最新记录的当天开始同步，以获取当天可能未同步完的后续K线
                start_date = latest_record.strftime('%Y%m%d')
            else:
                # 如果没有记录，则从上市日期开始全量同步
                start_date = config.START_DATE or stock.list_date.strftime('%Y%m%d')

            _sync_stock_data(stock.ts_code, start_date=start_date)
            pbar.update(1)
            
    session.close()
    print("所有股票增量同步完成。")


def _sync_stock_data(ts_code: str, start_date: str, end_date: str = None):
    """
    使用pro_bar接口获取并存储单个股票在指定时间范围内的30分钟K线数据。
    """
    try:
        df = ts.pro_bar(ts_code=ts_code, freq='30min', start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            return

        # 数据清洗和格式化
        df.rename(columns={'vol': 'vol', 'amount': 'amount'}, inplace=True)
        df['trade_time'] = pd.to_datetime(df['trade_time'])
        
        # 选择需要的列
        df = df[['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount']]
        
        # 批量插入数据库
        db.bulk_insert_data(df, db.Stock30Min)

    except Exception as e:
        print(f"同步 {ts_code} 数据时出错: {e}")

def fix_missing_data():
    """
    检查并修复缺失的交易日数据。
    这是一个复杂的功能，我们先实现一个简化版本：
    检查最近N天的数据完整性。
    """
    # 此功能较为复杂，将在后续迭代中实现。
    # 基本思路：
    # 1. 获取交易日历
    # 2. 对每只股票，获取其在数据库中的所有交易时间
    # 3. 对比交易日历和已有数据，找出缺失的交易日
    # 4. 对缺失的交易日，重新调用_sync_stock_data来获取数据
    print("数据修复功能待实现。")

if __name__ == '__main__':
    # 可以添加一些直接运行此脚本时的测试代码
    print("这是一个数据同步模块，请通过 main.py 来调用。")
    # 例如，测试更新股票列表
    # update_stock_basic()
    # full_sync()
    pass
