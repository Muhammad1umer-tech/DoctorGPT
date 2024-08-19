# Use the official Python image as a base image
# FROM python:3.11.9
FROM python:3.12.2

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
# Install dependencies
COPY . .

# Copy the rest of the application code to the working directory

# Run database migrations and collect static files
# RUN python manage.py migrate
# Expose the port that the Gunicorn app runs on
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]