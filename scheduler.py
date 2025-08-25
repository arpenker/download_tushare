from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from .data_sync import update_sync, update_sync_daily, fix_missing_data

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def daily_update_job():
    """
    定义每日增量更新的任务。
    将按顺序更新30分钟线和日线数据。
    """
    logging.info("开始执行每日定时增量更新任务...")
    try:
        logging.info("--- 开始更新30分钟K线数据 ---")
        update_sync()
        logging.info("--- 30分钟K线数据更新完成 ---")

        logging.info("--- 开始更新日线行情数据 ---")
        update_sync_daily()
        logging.info("--- 日线行情数据更新完成 ---")

        logging.info("每日定时增量更新任务全部执行成功。")
    except Exception as e:
        logging.error(f"每日定时增量更新任务执行失败: {e}", exc_info=True)

def main():
    """
    主函数，启动调度器。
    """
    # 检查Tushare Token和数据库密码是否已配置
    from . import config
    import sys
    if 'YOUR_TUSHARE_TOKEN' in config.TUSHARE_TOKEN:
        print("错误：请先在 config.py 文件中设置您的 TUSHARE_TOKEN。", file=sys.stderr)
        sys.exit(1)
    if 'YOUR_DATABASE_PASSWORD' in config.DB_CONFIG['password']:
        print("错误：请先在 config.py 文件中设置您的数据库密码。", file=sys.stderr)
        sys.exit(1)

    # 创建一个阻塞式调度器
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 添加定时任务
    # 触发器设置为：周一到周五，下午4点 (16:00) 执行
    # 这个时间点A股已经收盘，可以获取到当天的完整数据
    scheduler.add_job(
        daily_update_job,
        trigger=CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
        id='daily_stock_update',
        name='每日A股数据增量更新',
        replace_existing=True
    )

    # 添加每周数据完整性检查任务
    # 触发器设置为：每周日的凌晨2点执行
    scheduler.add_job(
        fix_missing_data,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='weekly_data_fix',
        name='每周数据完整性检查与修复',
        replace_existing=True
    )

    logging.info("调度器已启动。等待下一个执行时间点...")
    print("定时任务已设置。将在每个交易日下午16:00自动执行增量数据同步。")
    print("每周日凌晨02:00将执行一次数据完整性检查。")
    print("按 Ctrl+C 可以退出程序。")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("调度器已停止。")

if __name__ == '__main__':
    main()
