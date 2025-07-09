FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and ngrok
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install ngrok
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
    && apt-get update && apt-get install -y ngrok

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app

# Create pyngrok directory with proper permissions
RUN mkdir -p /home/app/.ngrok2
RUN chown -R app:app /home/app/.ngrok2

# Switch to non-root user
USER app

# Set environment variables for ngrok
ENV NGROK_CONFIG_PATH=/home/app/.ngrok2/ngrok.yml

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 