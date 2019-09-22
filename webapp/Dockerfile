FROM python:3.7
ADD . /home/

# Update and upgrade everything
RUN apt-get -y update && \
    apt-get -y upgrade


RUN pip install pip --upgrade 
RUN pip install -r /home/requirements.txt
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.3/en_core_sci_md-0.2.3.tar.gz
RUN chmod a+x /home/run.sh
