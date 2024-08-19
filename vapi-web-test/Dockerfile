# Use an official Node.js runtime as the base image
FROM node:18

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and yarn.lock files to the working directory
COPY package.json yarn.lock ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the application
RUN npm run build

# # Install a simple HTTP server to serve the built application
# RUN npm -g install serve

# Expose the port the app runs on
EXPOSE 9000

# Command to run the application
# CMD ["serve", "-s", "dist", "-l", "5000"]
CMD ["npm","run","start"]