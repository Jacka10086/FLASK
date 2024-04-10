# 使用官方Python镜像作为基础镜像
FROM python:3.8-slim

# 设置工作目录为 /app
WORKDIR /app

# 将当前目录下的所有文件复制到容器中的/app目录
COPY . /app

# 使用pip命令安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 由于您的应用可能依赖于静态文件和模板，确保它们也被包括在内
# 注意：COPY . /app 已经包括了 static 和 templates 目录

# 告诉 Docker 在运行容器时监听哪个端口
EXPOSE 5000

# 运行您的应用
CMD ["python", "app.py"]
