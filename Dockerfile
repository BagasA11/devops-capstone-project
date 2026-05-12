FROM python:3.9-slim 

# create working directory and install dependencies
WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy application content
COPY service/ ./service/

# add user and change ownnership all content of /app to theia
RUN useradd --uid 1000 theia && chown -R theia /app
# change user
USER theia

EXPOSE 8080

CMD [ "gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app" ]
