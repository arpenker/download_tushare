# A股日线及30分钟K线数据同步工具

本项目是一个使用Python编写的工具，用于从Tushare Pro获取所有A股的日线及30分钟K线数据，并将其存储到本地的MySQL数据库中。

## 主要功能

- **多周期数据下载**: 一次性获取所有股票的历史日线和30分钟K线数据。
- **增量数据更新**: 每日定时任务，自动获取当天最新的日线和30分钟K线数据。
- **进度条显示**: 在进行大量数据下载时，提供清晰的进度条。
- **数据表自动创建**: 首次运行时可自动创建所需的数据库和数据表。
- **定时任务**: 内置一个基于APScheduler的定时任务，可在每个交易日收盘后自动执行增量更新。
- **灵活的命令行接口**: 支持通过命令行参数执行不同的任务。
- **Docker一键部署**: 提供`docker-compose`配置，实现自动化部署和静默运行。

---

## Docker一键部署（推荐）

使用Docker是推荐的部署方式，它可以让您完全不用操心环境配置和程序运行。

**前提条件:**
- 已安装 [Docker](https://www.docker.com/get-started/)
- 已安装 [Docker Compose](https://docs.docker.com/compose/install/) (通常随Docker Desktop for Windows/Mac一起安装)

**部署步骤:**

**1. 配置**

将项目根目录下的 `.env.example` 文件复制一份并重命名为 `.env`。然后打开 `.env` 文件，填入您的个人信息：

```
# .env
TUSHARE_TOKEN=YOUR_TUSHARE_TOKEN_HERE
MYSQL_ROOT_PASSWORD=your_strong_password
```
- `TUSHARE_TOKEN`: 您的Tushare Pro API Token。
- `MYSQL_ROOT_PASSWORD`: 为您的数据库设置一个安全的密码。

**2. 启动服务**

在项目根目录下，打开命令行工具（如 PowerShell 或 CMD），运行以下命令：
```bash
docker-compose up -d
```
该命令会做以下事情：
- 在后台构建并启动Python应用容器和MySQL数据库容器。
- 数据库会自动创建，数据会持久化存储在Docker卷中。
- Python应用会自动开始执行定时任务，在每个交易日下午16:00进行增量同步。

**3. 执行首次全量同步**

服务启动后，您需要手动执行**两次**全量同步，分别获取30分钟和日线的全部历史数据。
打开一个新的命令行窗口，依次运行以下命令：

**同步30分钟K线历史数据 (非常耗时):**
```bash
docker-compose exec app python main.py full
```

**同步日线历史数据 (非常耗时):**
```bash
docker-compose exec app python main.py full_daily
```
完成后，未来的数据将由定时任务自动增量同步。

**4. 日常使用**

- **查看日志**: 如果想观察程序的运行状态，可以查看应用日志。
  ```bash
  docker-compose logs -f app
  ```
- **连接数据库**: 您可以使用任何MySQL客户端（如Navicat, DataGrip, DBeaver）连接到数据库来查看和分析数据。
  - **主机**: `127.0.0.1`
  - **端口**: `3307` (注意，已映射到3307以避免与本地MySQL冲突)
  - **用户**: `root`
  - **密码**: 您在 `.env` 文件中设置的 `MYSQL_ROOT_PASSWORD`
  - **数据库**: `stock_data`

- **停止服务**: 如果您想停止所有服务，可以运行：
  ```bash
  docker-compose down
  ```

---

## 手动安装与使用（旧版）

如果您不想使用Docker，也可以按照传统方式手动部署。

### 环境要求

- Python 3.7+
- MySQL 5.7+ 或 MariaDB

### 安装与配置

(步骤省略，请参考Docker部署方式中的配置说明)

### 使用说明

**1. 初始化数据库表**
```bash
python main.py initdb
```

**2. 全量同步历史数据**
```bash
# 同步30分钟线
python main.py full

# 同步日线
python main.py full_daily
```

**3. 增量更新数据**
```bash
# 增量更新30分钟线
python main.py update

# 增量更新日线
python main.py update_daily
```

**4. 运行定时任务**
```bash
# 这将同时更新30分钟线和日线数据
python scheduler.py
```
