# Use a Python base image for the arm64 architecture
FROM arm64v8/python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y python3-pip python3-evdev libcamera-tools build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy your script
COPY main2.py .

# Install Python dependencies
RUN pip3 install requests evdev

# Create required directories
RUN mkdir -p /var/log/robot_logger

# Define the command to run
CMD ["python3", "main2.py"]
