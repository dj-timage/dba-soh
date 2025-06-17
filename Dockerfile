# Use the official Python image as the base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Specify the command to run your Python script
CMD ["python", "dbasoh.py"]


# Install cron
RUN apt-get update && apt-get install -y cron

# Add your cron job
RUN echo "0 0 * * * python /app/dbasoh.py" > /etc/cron.d/dbasoh-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/dbasoh-cron

# Apply the cron job
RUN crontab /etc/cron.d/dbasoh-cron

# Start cron in the foreground
CMD ["cron", "-f"]