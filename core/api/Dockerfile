FROM node:18-alpine

WORKDIR /app

# Install Docker CLI (for managing containers)
RUN apk add --no-cache docker-cli

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy source code
COPY . .

# Create required directories
RUN mkdir -p /app/tools /app/data

# Expose port
EXPOSE 3001

# Start the application
CMD ["npm", "start"]
