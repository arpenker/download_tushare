# ------------------ Tushare Configuration ------------------
# 在这里填入你的Tushare Pro API Token。
# 你可以访问 https://tushare.pro/user/token 来获取你的token。
TUSHARE_TOKEN = "YOUR_TUSHARE_TOKEN_HERE"

# ------------------ MySQL Database Configuration ------------------
# 在这里填入你的MySQL数据库连接信息。
DB_CONFIG = {
    'host': '127.0.0.1',  # 数据库主机地址
    'port': 3306,         # 端口号
    'user': 'root',       # 数据库用户名
    'password': 'YOUR_DATABASE_PASSWORD_HERE', # 数据库密码
    'database': 'stock_data', # 数据库名称
    'charset': 'utf8mb4'      # 字符集
}

# ------------------ Data Sync Configuration ------------------
# 获取历史数据时的起始日期
# 如果设置为None，将从股票的上市日期开始获取
START_DATE = "2010-01-01"

# 每次API请求的K线数量
# Tushare pro接口单次提取最多5000条
BARS_PER_REQUEST = 5000
