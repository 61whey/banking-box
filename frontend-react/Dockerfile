# Multi-stage build for production
FROM oven/bun:1 AS builder

WORKDIR /app

# Copy package files
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Build arguments for API URL
ARG VITE_API_URL=http://localhost:54080
ARG VITE_BANK_CODE=VBANK

# Set environment variables for build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_BANK_CODE=${VITE_BANK_CODE}

# Build application
RUN bun run build

# Production stage
FROM oven/bun:1-alpine

WORKDIR /app

# Copy built application from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules/vite ./node_modules/vite

# Install only vite for preview server (lightweight)
RUN bun add -g vite || bun install vite

# Expose port
EXPOSE 3000

# Start preview server
CMD ["bunx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]

