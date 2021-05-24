FROM python:3.9

# Import MongoDB public GPG key AND create a MongoDB list file
RUN wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list

# Update apt-get sources AND install MongoDB
RUN apt-get update && apt-get install -y mongodb-org

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY run.py .

ENTRYPOINT ["python", "run.py"]