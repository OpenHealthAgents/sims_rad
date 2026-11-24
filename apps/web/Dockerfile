# Stage 1: Build Vite & Lit web application
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts || npm install

COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD wget -q -O - http://127.0.0.1:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
