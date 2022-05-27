FROM python:3.7
ADD . /home/

# Update and upgrade everything
RUN apt-get -y update && \
    apt-get -y upgrade

# install vim as its annoying not to have an editor
RUN apt-get install -y vim

# Get node and npm
RUN apt-get install curl && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install nodejs && \
    npm install -g npm@latest

# Build frontend
WORKDIR /home/frontend
RUN npm install && npm run build

# Build backend
WORKDIR /home/api
RUN pip install pip --upgrade 
RUN pip install -r /home/requirements.txt
RUN python -m spacy download en_core_web_md
RUN chmod a+x /home/run.sh
