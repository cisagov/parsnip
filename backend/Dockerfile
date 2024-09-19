# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /opt
WORKDIR /opt

RUN apt update
RUN apt install -y build-essential libgraphviz-dev

# Copy the current directory contents into the container at /opt
ADD ./requirements.txt /opt/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r /opt/requirements.txt

# Run a terminal when the container starts
CMD ["/bin/bash"]
