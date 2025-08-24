# A股30分钟K线数据同步工具

本项目是一个使用Python编写的工具，用于从Tushare Pro获取所有A股的30分钟K线数据，并将其存储到本地的MySQL数据库中。

## 主要功能

- **全量数据下载**: 一次性获取指定股票或所有股票的全部历史30分钟K线数据。
- **增量数据更新**: 每日定时任务，自动获取当天最新的K线数据，并补充到数据库中。
- **进度条显示**: 在进行大量数据下载时，提供清晰的进度条。
- **数据表自动创建**: 首次运行时可自动创建所需的数据库和数据表。
- **定时任务**: 内置一个基于APScheduler的定时任务，可在每个交易日收盘后自动执行增量更新。
- **灵活的命令行接口**: 支持通过命令行参数执行不同的任务。

## 环境要求

- Python 3.7+
- MySQL 5.7+ 或 MariaDB

## 安装与配置

**1. 获取代码**

克隆或下载本项目到你的本地机器。

**2. 安装依赖**

进入项目根目录，通过 `requirements.txt` 文件安装所有必需的Python库。

```bash
pip install -r requirements.txt
```

**3. 配置 Tushare Token 和数据库**

打开 `download_tushare/config.py` 文件，填入你的个人信息：

- `TUSHARE_TOKEN`: 你的Tushare Pro API Token。你可以在 [Tushare Pro官网](https://tushare.pro/user/token) 免费注册并获取。
- `DB_CONFIG`: 你的MySQL数据库连接信息，包括主机、端口、用户名、密码和数据库名。

**4. 创建数据库**

在你的MySQL服务器中，手动创建一个数据库。数据库的名称应与你在 `config.py` 中 `DB_CONFIG['database']` 字段设置的名称一致。

例如，如果你设置的数据库名是 `stock_data`，则执行以下SQL命令：

```sql
CREATE DATABASE stock_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 使用说明

本工具可以通过 `python -m download_tushare` 命令来运行，后跟不同的子命令。

**1. 初始化数据库表**

在第一次运行时，你需要初始化数据库，创建所需的数据表。

```bash
python -m download_tushare initdb
```
该命令会根据 `database.py` 中的定义，自动创建 `stock_basic` 和 `stock_30min` 两张表。

**2. 全量同步历史数据**

如果你是第一次使用，或者想要完整地获取所有历史数据，可以执行全量同步。

**警告**: 此过程会遍历所有A股，下载它们自上市以来的全部30分钟K线数据，将消耗大量时间和网络流量，并对Tushare积分有一定要求。

```bash
python -m download_tushare full
```

**3. 增量更新数据**

用于获取最新的数据。它会自动查找每只股票在数据库中的最新记录，并从该时间点之后开始同步。如果某只股票是新加入的，则会自动进行全量同步。

建议每日收盘后执行此命令。

```bash
python -m download_tushare update
```

## 运行定时任务

为了实现自动化更新，你可以直接运行 `scheduler.py` 脚本。它会启动一个常驻进程，在每个交易日（周一至周五）的下午16:00自动执行增量更新任务。

```bash
python -m download_tushare.scheduler
```

你可以使用 `nohup` (Linux/macOS) 或其他工具让它在后台持续运行。

```bash
nohup python -m download_tushare.scheduler > scheduler.log 2>&1 &
```

按 `Ctrl+C` 可以停止调度器。
