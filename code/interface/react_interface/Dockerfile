FROM node:20-bookworm-slim AS build
WORKDIR /app

# Install dependencies (no dev cache in final image)
COPY package.json package-lock.json ./
RUN npm ci

# Build the production bundle
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS prod
WORKDIR /usr/share/nginx/html

# Remove default nginx content and config
RUN rm -rf ./* /etc/nginx/conf.d/*

# Copy build output
COPY --from=build /app/dist ./

# Minimal nginx config for SPA
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }
}
EOF

# Prepare nginx runtime dirs for nginx worker user (uid 101)
RUN mkdir -p /var/cache/nginx /var/run/nginx /run/nginx \
    && chown -R 101:101 /var/cache/nginx /var/run/nginx /run/nginx

# Expose the web port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
