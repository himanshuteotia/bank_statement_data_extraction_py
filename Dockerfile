FROM ubuntu:latest
MAINTAINER Himanshu Teotia "himanshuteotia7@gmail.com"
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN python3 -m spacy download en_core_web_lg
ENTRYPOINT ["python3"]
CMD ["index.py"]