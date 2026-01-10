FROM node:18-alpine AS builder

WORKDIR /app

# Build argument for API URL
ARG VITE_API_BASE_URL=https://inspro-mes.ru

# Copy package files
COPY package*.json ./

# Install dependencies (using npm install for cross-platform compatibility)
RUN npm install

# Copy source code
COPY . .

# Set environment variable for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build production bundle
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

