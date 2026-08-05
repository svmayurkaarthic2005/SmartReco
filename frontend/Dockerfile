# Node.js alpine image for frontend development/preview
FROM node:18-alpine

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY . .

# Expose Vite server port
EXPOSE 3000

# Start Vite server listening on port 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
