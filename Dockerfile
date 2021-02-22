FROM python:3.8.1

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . /app

RUN pip install wheel
RUN pip install -r requirements.txt

# ENTRYPOINT ["python3 app.py"]
CMD ["python", "app.py"]