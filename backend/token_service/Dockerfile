FROM python:3.11-slim

# Build from repo root so ../../packages/ in requirements.txt resolves
WORKDIR /workspace
COPY . .
WORKDIR /workspace/backend/token_service
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
