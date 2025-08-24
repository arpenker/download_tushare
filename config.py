import os

# ------------------ Tushare Configuration ------------------
# 优先从环境变量获取Tushare Pro API Token，如果不存在则使用下面的默认值。
# 在Docker环境中，这个值将由docker-compose.yml文件注入。
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "YOUR_TUSHARE_TOKEN_HERE")

# ------------------ MySQL Database Configuration ------------------
# 优先从环境变量获取数据库配置，这在Docker部署时非常有用。
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "127.0.0.1"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", "YOUR_DATABASE_PASSWORD_HERE"),
    'database': os.getenv("DB_DATABASE", "stock_data"),
    'charset': 'utf8mb4'
}

# ------------------ Data Sync Configuration ------------------
# 获取历史数据时的起始日期
# 如果设置为None，将从股票的上市日期开始获取
START_DATE = "2010-01-01"
