# Start with official Python base image.
FROM python:3.10.6

# Set current working directory.
WORKDIR /code

# Copy requirements to working directory.
COPY ./requirements.txt /code/requirements.txt

# Install package dependecies in the requirements file. Tell pip to not save
# packages locally. Upgrade packages if already installed. Use Docker cache
# when available, saves time for building image again for deployment.
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Maybe putting the database here will work?
COPY ./database.sqlite /code/database.sqlite

# Copy app to working directory. As this has the code which changes frequently,
# the Docker cache won't be used or any following steps easily. Important to
# put this near the end to optimize container image build times.
COPY ./api /code/api

# Set command to run the uvicorn server, taking in a list of strings as args,
# which will be run from the current working directory.
CMD ["uvicorn", "api.main:holy_api", "--host", "0.0.0.0", "--port", "8080"]