# 使用官方的 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到工作目录中
COPY requirements.txt .

# 安装所需的包
# 使用 --no-cache-dir 来减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录内容复制到容器的 /app 中
COPY . .

# 设置容器启动时执行的命令
# 运行调度器，它会按计划自动执行增量同步任务
CMD ["python", "scheduler.py"]
