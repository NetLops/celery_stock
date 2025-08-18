FROM python:3.11-slim

WORKDIR /app

# 配置国内源
#RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
#     sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

 RUN echo "deb http://mirrors.aliyun.com/debian $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2) main contrib non-free" > /etc/apt/sources.list \
 && echo "deb http://mirrors.aliyun.com/debian-security $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2)-security main contrib non-free" >> /etc/apt/sources.list \
 && echo "deb http://mirrors.aliyun.com/debian $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2)-updates main contrib non-free" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 配置pip国内源并安装Python依赖
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]