FROM python:3.11-slim

# Install ffmpeg + any required OS packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirror-pypi.runflare.com/simple -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
