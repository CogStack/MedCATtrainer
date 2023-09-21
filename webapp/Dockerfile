FROM python:3.11

# Update and upgrade everything
RUN apt-get update -y && \
    apt-get upgrade -y

# install vim as its annoying not to have an editor
RUN apt-get install -y vim

# Get node and npm
RUN apt install -y nodejs && apt install -y npm

# Install Rust - for tokenziers dep in medcat.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

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
