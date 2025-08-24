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
        description="Tushare A股30分钟K线数据同步工具。",
        epilog="使用 'python -m download_tushare <command> --help' 来查看具体命令的帮助信息。"
    )

    # 创建一个子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='可用的命令')
    subparsers.required = True

    # 1. `initdb` 命令
    parser_initdb = subparsers.add_parser('initdb', help='初始化数据库，创建数据表。')
    parser_initdb.set_defaults(func=database.init_db)

    # 2. `full` 命令
    parser_full = subparsers.add_parser('full', help='全量同步所有股票的30分钟K线历史数据。')
    parser_full.set_defaults(func=data_sync.full_sync)

    # 3. `update` 命令
    parser_update = subparsers.add_parser('update', help='增量同步所有股票的最新30分钟K线数据。')
    parser_update.set_defaults(func=data_sync.update_sync)
    
    # 4. `fix` 命令 (占位)
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
