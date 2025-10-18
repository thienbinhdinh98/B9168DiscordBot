FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy src directory to /app
COPY src/ .

# Create data directories (they'll be mounted as volumes)
RUN mkdir -p /app/data/qidian /app/logs

# Setup user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run bot from /app (where we copied src/ contents)
CMD ["python", "-u", "bot.py"]