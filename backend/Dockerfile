# Use Python 3.11 slim
FROM python:3.11-slim

# Set workdir
WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8000

# Command for dev
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]