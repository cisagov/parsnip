# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /opt
WORKDIR /opt

# Copy the current directory contents into the container at /opt
ADD ./requirements.txt /opt/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r /opt/requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Run app.py when the container launches
#CMD ["python", "app.py"]
CMD ["/bin/bash"]