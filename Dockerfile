# OGP Biblioteca Virtual Scraper
#
# Build:
#   docker build -t ogp-scraper .
#
# Run (API mode):
#   docker run --rm -v $(pwd)/output:/app/scraper/output ogp-scraper
#
# Run (Selenium mode):
#   docker run --rm -e OGP_USE_SELENIUM=1 -v $(pwd)/output:/app/scraper/output ogp-scraper python -m scraper.main selenium
#
# Run (all):
#   docker run --rm -e OGP_USE_SELENIUM=1 -v $(pwd)/output:/app/scraper/output ogp-scraper python -m scraper.main all

FROM python:3.12-slim

WORKDIR /app

# Install system deps for Selenium/Chrome (optional but included)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: explore mode
CMD ["python", "-m", "scraper.main"]
