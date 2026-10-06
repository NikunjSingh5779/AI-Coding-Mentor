# Frontend Development
FROM node:24-alpine as frontend-dev

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm@11.8.0

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Command for development
CMD ["pnpm", "dev", "--host"]

# Frontend Production Build
FROM node:24-alpine as frontend-build

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm@11.8.0

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build application
RUN pnpm build

# Production Frontend
FROM nginx:alpine as frontend-prod

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets
COPY --from=frontend-build /app/dist /usr/share/nginx/html


# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q -O - http://localhost/health >/dev/null || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]