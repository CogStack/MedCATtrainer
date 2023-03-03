FROM python:3.10

# Update and upgrade everything
RUN apt-get -y update && \
    apt-get -y upgrade

# install vim as its annoying not to have an editor
RUN apt-get -y install vim

# Get node and npm
RUN apt-get install curl && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install nodejs && \
    npm install -g npm@latest

# Copy project
WORKDIR /home
COPY ./ .

# Build frontend
WORKDIR /home/frontend
RUN npm install && npm run build

# Install requirements for backend
WORKDIR /home/
RUN pip install pip --upgrade 
RUN pip install -r requirements.txt
ARG SPACY_MODELS="en_core_web_md"
RUN for SPACY_MODEL in ${SPACY_MODELS}; do python -m spacy download ${SPACY_MODEL}; done

WORKDIR /home/api/
RUN chmod a+x /home/run.sh
