FROM python:3.7

COPY . /webapp
# Set the pythonpath
WORKDIR /webapp

RUN pip install -r requirements.txt

# Get the spacy and scipspacy model
RUN python -m spacy download en_core_web_sm
RUN pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.0/en_core_sci_md-0.2.0.tar.gz

# Get the MedMen models
RUN mkdir /models
#RUN wget "https://s3-eu-west-1.amazonaws.com/zkcl/med_ann_norm.dat" -P /models/
#RUN wget "https://s3-eu-west-1.amazonaws.com/zkcl/med_ann_norm_dict.dat" -P /models/

# Build the db
RUN python manage.py makemigrations && \
    python manage.py makemigrations trainerapp && \
    python manage.py migrate && \
    python manage.py migrate trainerapp

# This should not be done like this, but who cares
RUN python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', password='admin', email='test@test.com')"; exit 0
