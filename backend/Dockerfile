FROM python:3.11-slim

# System deps for mediapipe (libgl, libglib for opencv-headless transitive,
# but we keep it minimal). MediaPipe wheels need a few shared libs at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user — security baseline.
RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

USER app

EXPOSE 8000

# Single worker keeps the in-memory frame bus consistent. Scale by running
# multiple containers behind a shared Redis bus (see frame_store.py docstring).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
