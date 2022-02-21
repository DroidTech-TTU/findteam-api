FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN mkdir /pictures
VOLUME /pictures

EXPOSE 80/tcp

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]