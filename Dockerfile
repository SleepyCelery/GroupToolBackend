# 使用官方Python 3.9镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 先复制requirements.txt并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 然后复制其他文件
COPY . .

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# 运行数据库初始化（如果需要）
# RUN python -c "from models import SQLModel; SQLModel.metadata.create_all(engine)"

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
