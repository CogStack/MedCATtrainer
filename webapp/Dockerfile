FROM python:3.7

# Create the required folders
RUN mkdir -p /webapp/data  && \
    mkdir -p /webapp/data/input && \
    mkdir -p /webapp/data/output && \
    mkdir -p /webapp/data/incomplete && \
    mkdir -p /webapp/models


# Copy everything
COPY . /webapp

# Set vocab_path
ENV VOCAB_PATH=/webapp/models/vocab_base.dat
ENV VOCAB_URL=https://s3-eu-west-1.amazonaws.com/zkcl/vocab.dat

ENV CDB_PATH=/webapp/models/cdb_base.dat
ENV CDB_URL=https://s3-eu-west-1.amazonaws.com/zkcl/cdb-medmen-trained.dat

# Set the pythonpath
WORKDIR /webapp

RUN pip install -r requirements.txt

# Get the spacy and scipspacy model
RUN python -m spacy download en_core_web_sm
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_core_sci_md-0.2.0.tar.gz

# Build the db
RUN python manage.py makemigrations && \
    python manage.py makemigrations trainerapp && \
    python manage.py migrate && \
    python manage.py migrate trainerapp

# This should not be done like this, but who cares
RUN python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', password='admin', email='test@test.com')"; exit 0
