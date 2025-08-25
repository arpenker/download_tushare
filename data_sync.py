import tushare as ts
import pandas as pd
import time
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
    包含API请求重试逻辑。
    """
    for i in range(3): # 重试3次
        try:
            df = ts.pro_bar(ts_code=ts_code, freq='30min', start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return # 如果没有数据，直接返回

            # 数据清洗和格式化
            df.rename(columns={'vol': 'vol', 'amount': 'amount'}, inplace=True)
            df['trade_time'] = pd.to_datetime(df['trade_time'])

            # 选择需要的列
            df = df[['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount']]

            # 批量插入数据库
            db.bulk_insert_data(df, db.Stock30Min)

            return # 成功后直接退出函数

        except Exception as e:
            print(f"同步30分钟线 {ts_code} 时出错 (第 {i+1} 次尝试): {e}")
            if i < 2: # 如果不是最后一次尝试，则等待后重试
                print("等待3秒后重试...")
                time.sleep(3)

    print(f"同步30分钟线 {ts_code} 失败3次，已跳过。")


# ------------------ Daily Data Sync Functions ------------------

def full_sync_daily():
    """
    全量同步所有A股的日线行情数据。
    """
    print("开始全量同步日线行情数据，这是一个非常耗时的操作。")
    update_stock_basic()
    stocks_to_sync = get_stock_list()

    with tqdm(total=len(stocks_to_sync), desc="日线全量同步进度") as pbar:
        for stock in stocks_to_sync:
            pbar.set_description(f"正在同步日线 {stock.ts_code}")
            _sync_stock_daily_data(stock.ts_code, start_date=config.START_DATE or stock.list_date.strftime('%Y%m%d'))
            pbar.update(1)
    print("所有股票日线全量同步完成。")


def update_sync_daily():
    """
    增量同步所有A股的日线行情数据。
    """
    print("开始增量同步日线行情数据...")
    update_stock_basic()
    stocks_to_sync = get_stock_list()

    session = db.get_session()

    print("正在查询所有股票的最新日线记录时间...")
    latest_records_query = session.query(
        db.StockDaily.ts_code,
        func.max(db.StockDaily.trade_date)
    ).group_by(db.StockDaily.ts_code).all()

    latest_records_map = {ts_code: max_date for ts_code, max_date in latest_records_query}
    print("查询完成。")

    with tqdm(total=len(stocks_to_sync), desc="日线增量同步进度") as pbar:
        for stock in stocks_to_sync:
            pbar.set_description(f"增量同步日线 {stock.ts_code}")

            latest_record = latest_records_map.get(stock.ts_code)

            if latest_record:
                # 从最新记录的后一天开始同步
                start_date = (latest_record + timedelta(days=1)).strftime('%Y%m%d')
            else:
                # 如果没有记录，则从上市日期开始全量同步
                start_date = config.START_DATE or stock.list_date.strftime('%Y%m%d')

            _sync_stock_daily_data(stock.ts_code, start_date=start_date)
            pbar.update(1)

    session.close()
    print("所有股票日线增量同步完成。")


def _sync_stock_daily_data(ts_code: str, start_date: str, end_date: str = None):
    """
    使用daily接口获取并存储单个股票的日线行情数据。
    包含API请求重试逻辑。
    """
    for i in range(3): # 重试3次
        try:
            # Tushare建议使用pro.daily接口获取日线数据
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return # 如果没有数据，直接返回

            # 数据清洗和格式化
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 选择我们数据库中定义的列
            columns_to_keep = [
                'ts_code', 'trade_date', 'open', 'high', 'low', 'close',
                'pre_close', 'change', 'pct_chg', 'vol', 'amount'
            ]
            df = df[columns_to_keep]

            # 批量插入数据库
            db.bulk_insert_data(df, db.StockDaily)

            return # 成功后直接退出函数

        except Exception as e:
            print(f"同步日线 {ts_code} 数据时出错 (第 {i+1} 次尝试): {e}")
            if i < 2: # 如果不是最后一次尝试，则等待后重试
                print("等待3秒后重试...")
                time.sleep(3)

    print(f"同步日线 {ts_code} 失败3次，已跳过。")


def fix_missing_data():
    """
    检查并修复数据库中缺失的交易日数据。
    该函数会对比交易日历和已存数据，找出空洞并尝试重新获取。
    这是一个资源密集型操作，建议在非交易时间执行。
    """
    print("--- 开始执行数据完整性检查与修复任务 ---")

    # 1. 获取交易日历
    print("正在获取交易日历...")
    try:
        trade_cal = pro.trade_cal(exchange='SSE', start_date=config.START_DATE, end_date=datetime.now().strftime('%Y%m%d'))
        trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].apply(lambda x: datetime.strptime(x, '%Y%m%d').date()).tolist()
        trade_dates_set = set(trade_dates)
        print(f"获取到 {len(trade_dates)} 个交易日。")
    except Exception as e:
        print(f"获取交易日历失败: {e}")
        return

    # 2. 获取所有股票列表
    stocks = get_stock_list()
    if not stocks:
        print("股票基础信息为空，无法进行检查。")
        return

    session = db.get_session()

    # 3. 获取所有已存在的日线数据记录
    print("正在查询所有已存在的日线数据记录...")
    existing_daily_query = session.query(db.StockDaily.ts_code, db.StockDaily.trade_date).all()
    existing_daily_set = set(existing_daily_query)
    print("查询完成。")

    # 4. 识别日线数据缺口
    gaps_to_fix = []
    print("开始检查日线数据缺口...")
    with tqdm(total=len(stocks), desc="检查日线缺口") as pbar:
        for stock in stocks:
            pbar.set_description(f"检查日线 {stock.ts_code}")
            list_date = stock.list_date

            # 获取此股票需要检查的交易日范围
            relevant_trade_dates = {d for d in trade_dates_set if d >= list_date}

            # 获取此股票已有的数据日期
            stock_existing_dates = {date for ts_code, date in existing_daily_set if ts_code == stock.ts_code}

            missing_dates = relevant_trade_dates - stock_existing_dates

            for missing_date in missing_dates:
                gaps_to_fix.append({'ts_code': stock.ts_code, 'date': missing_date.strftime('%Y%m%d')})

            pbar.update(1)

    print(f"发现 {len(gaps_to_fix)} 个日线数据缺口需要修复。")

    # 5. 修复日线数据缺口
    if gaps_to_fix:
        with tqdm(total=len(gaps_to_fix), desc="修复日线缺口") as pbar:
            for gap in gaps_to_fix:
                pbar.set_description(f"修复日线 {gap['ts_code']} on {gap['date']}")
                _sync_stock_daily_data(gap['ts_code'], start_date=gap['date'], end_date=gap['date'])
                pbar.update(1)

    # TODO: 添加对30分钟线数据的检查和修复逻辑。目前为简化，暂不实现。
    # 30分钟线的逻辑更复杂，因为一天有多条记录。
    # 一个简单的策略是：如果某只股票某天的日线数据是补上的，那么也重新获取那天的30分钟线数据。

    session.close()
    print("--- 数据完整性检查与修复任务完成 ---")

if __name__ == '__main__':
    # 可以添加一些直接运行此脚本时的测试代码
    print("这是一个数据同步模块，请通过 main.py 来调用。")
    # 例如，测试更新股票列表
    # update_stock_basic()
    # full_sync()
    pass
