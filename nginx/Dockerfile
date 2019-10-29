FROM nginx
# Add configuration
RUN rm /etc/nginx/conf.d/default.conf
ADD nginx.conf /etc/nginx/nginx.conf
# Add site
RUN mkdir /etc/nginx/sites-enabled/
ADD sites-enabled/ /etc/nginx/sites-enabled
