# Optimised multi-stage docker build for cogstacksystems/medcat-trainer
# https://github.com/CogStack/MedCATtrainer/

# First stage: Build Vue.js frontend using node base image
# Copy only /home/frontend/dist into next stage - saves ~450MB
FROM node:16-slim as node_image
WORKDIR /home
COPY ./frontend /home/frontend
RUN cd /home/frontend \
    && npm install -g npm@latest \
    && npm install \
    && npm run build


# Second (Final) stage
FROM python:3.10

# Create a non-root user to install and run app
RUN groupadd -g 999 appuser \
    && useradd --create-home -r -u 999 -g appuser appuser

# Let the non-root user own the /home directory
RUN chown appuser:appuser /home

# Switch to non-root user for rest of the build
USER appuser

# Append to path to avoid pip complaining
ENV PATH=$PATH:/home/appuser/.local/bin

# Set working directory to /home. Everything will be copied/installed here. 
WORKDIR /home

# Copy requirements.txt and install requirements for backend
COPY --chown=appuser:appuser requirements.txt requirements.txt

# Don't cache pip packages - saves ~900MB
ARG SPACY_MODELS="en_core_web_md"
RUN pip install pip --upgrade --no-cache-dir \
    && pip install -r requirements.txt --no-cache-dir \
    && rm requirements.txt \
    && for SPACY_MODEL in ${SPACY_MODELS}; do python -m spacy download ${SPACY_MODEL}; done

# Copy over only the files and folders that are required
# This creates multiple layers but avoids copying entire frontend into this layer
COPY --chown=appuser:appuser load_examples.py run.sh ./
COPY --chown=appuser:appuser ./api ./api
COPY --from=node_image --chown=appuser:appuser /home/frontend/dist /home/frontend/dist

# Make run.sh executable
RUN chmod a+x run.sh

# Expose port 8000 - although this can also be done in docker-compose/helm
EXPOSE 8000

# Set default CMD. This can be overridden in docker-compose/helm.
# run.sh has been edited to fix path to manage.py
CMD run.sh
