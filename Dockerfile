FROM python:3.12
WORKDIR /app
# ENV KG_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src .
RUN chmod +x entry_point.sh
ENTRYPOINT ["./entry_point.sh"]