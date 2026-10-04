# Frontend Development
FROM node:18-alpine as frontend-dev

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 5173

# Command for development
CMD ["pnpm", "dev"]

# Frontend Production Build
FROM node:18-alpine as frontend-build

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install

# Copy source code
COPY frontend/ .

# Build application
RUN pnpm build

# Production Frontend
FROM nginx:alpine as frontend-prod

# Copy custom nginx config
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# Copy built assets
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Copy environment template
COPY frontend/env.template.js /usr/share/nginx/html/env.template.js

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]