FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt . && pip install --no-cache-dir -r requirements.txt
COPY app/src/main/python/ /app/backend/
COPY app/src/main/assets/ /app/assets/
ENV TPV_FRONTEND_DIR=/app/assets TPV_PORT=5000
EXPOSE 5000
CMD ["python3","/app/backend/app.py"]
