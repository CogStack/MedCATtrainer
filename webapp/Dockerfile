FROM python:3.7
ADD . /home/

# Update and upgrade everything
RUN apt-get -y update && \
    apt-get -y upgrade

# Get node and npm
RUN apt-get install curl && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install nodejs && \
    npm install -g npm@latest

# Build frontend
WORKDIR /home/frontend
#RUN npm install && npm rebuild node-sass && npm run build
RUN npm install && npm uninstall node-sass && npm install node-sass@4.12.0 && npm run build
# Build backend
WORKDIR /home/api
RUN pip install pip --upgrade 
RUN pip install -r /home/requirements.txt
RUN pip install https://zkcl.s3-eu-west-1.amazonaws.com/en_core_sci_lg-0.3.0.tar.gz
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.3.0/en_core_sci_md-0.3.0.tar.gz
RUN chmod a+x /home/run.sh
