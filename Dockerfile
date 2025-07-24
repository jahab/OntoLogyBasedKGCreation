FROM python:3.12
WORKDIR /app
# ENV KG_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY src .
# CMD ["python","app.py"]