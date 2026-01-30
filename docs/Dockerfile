# Production Dockerfile for Docusaurus
# Multi-stage build for optimized image size

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Accept LOCALE as build arg
ARG LOCALE=en

# Build the static site
RUN npm run build

# Production stage - serve with lightweight server
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/build ./build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --spider -q http://localhost:3000 || exit 1

# Serve the static files
CMD ["serve", "-s", "build", "-l", "3000"]
