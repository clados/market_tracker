# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install all dependencies (needed for build)
RUN npm install

# Copy source code
COPY frontend/ .

# Set build-time environment variables
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

# Build the application
RUN npm run build

# Production stage - serve with a simple HTTP server
FROM node:18-alpine

WORKDIR /app

# Install a simple HTTP server
RUN npm install -g serve

# Copy built application
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Start the server
CMD ["serve", "-s", "dist", "-l", "5173"] 