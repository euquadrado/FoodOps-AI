FROM python:3.12-slim
WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV RUFF_CACHE_DIR=/tmp/ruff PYTEST_ADDOPTS="-o cache_dir=/tmp/pytest-cache"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home foodops
USER foodops
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
