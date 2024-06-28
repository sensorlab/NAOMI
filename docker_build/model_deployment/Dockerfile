# Use an official Python runtime as a parent image
FROM python:3.10

WORKDIR /app

# Install any needed packages specified in requirements.txt, append your dependencies to requirements.txt
RUN pip install requirements.txt

ADD . /app
EXPOSE 8000

# Run api-endpoint.py with uvicorn when the container launches
CMD ["uvicorn", "api-endpoint:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-concurrency", "8000", "--log-level", "error", "--backlog", "8000"]
