import argparse
import sys

from . import database
from . import data_sync

def main():
    """
    主函数，处理命令行参数。
    """
    # 创建一个顶层解析器
    parser = argparse.ArgumentParser(
        description="Tushare A股日线及30分钟K线数据同步工具。",
        epilog="使用 'python main.py <command> --help' 来查看具体命令的帮助信息。"
    )

    # 创建一个子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='可用的命令')
    subparsers.required = True

    # --- 通用命令 ---
    parser_initdb = subparsers.add_parser('initdb', help='初始化数据库，创建所有数据表。')
    parser_initdb.set_defaults(func=database.init_db)

    # --- 30分钟线命令 ---
    parser_full_30min = subparsers.add_parser('full', help='全量同步所有股票的30分钟K线历史数据。')
    parser_full_30min.set_defaults(func=data_sync.full_sync)

    parser_update_30min = subparsers.add_parser('update', help='增量同步所有股票的最新30分钟K线数据。')
    parser_update_30min.set_defaults(func=data_sync.update_sync)

    # --- 日线命令 ---
    parser_full_daily = subparsers.add_parser('full_daily', help='全量同步所有股票的日线历史数据。')
    parser_full_daily.set_defaults(func=data_sync.full_sync_daily)

    parser_update_daily = subparsers.add_parser('update_daily', help='增量同步所有股票的最新日线数据。')
    parser_update_daily.set_defaults(func=data_sync.update_sync_daily)
    
    # --- 其他命令 ---
    parser_fix = subparsers.add_parser('fix', help='检查并修复缺失的K线数据（功能待实现）。')
    parser_fix.set_defaults(func=data_sync.fix_missing_data)

    # 解析参数
    args = parser.parse_args()

    # 检查Tushare Token和数据库密码是否已配置
    from . import config
    if 'YOUR_TUSHARE_TOKEN' in config.TUSHARE_TOKEN:
        print("错误：请先在 config.py 文件中设置您的 TUSHARE_TOKEN。", file=sys.stderr)
        sys.exit(1)
    if 'YOUR_DATABASE_PASSWORD' in config.DB_CONFIG['password']:
        print("错误：请先在 config.py 文件中设置您的数据库密码。", file=sys.stderr)
        sys.exit(1)

    # 执行相应的函数
    if hasattr(args, 'func'):
        args.func()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
