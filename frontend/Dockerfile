FROM node:18-alpine

WORKDIR /app

# 配置npm国内源
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx提供静态文件服务
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]