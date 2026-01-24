FROM python:3.11
WORKDIR /app
RUN pip install gunicorn==23.0.0
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install -r /app/requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "tech_support.wsgi"]