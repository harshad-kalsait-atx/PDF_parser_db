fastapi_parquet_app/
├── app/
│   ├── main.py
│   ├── utils.py
│   └── storage/
│       └── user_{user_id}/
│           ├── files.parquet
│           └── projects/
│               └── {project_name}/
│                   ├── {project_name}.pdf
│                   ├── {project_name}_updated.json
│                   └── {project_name}_updated.txt
├── requirements.txt
└── README.md


# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
