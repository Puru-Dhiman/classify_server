FROM python:3
WORKDIR /user/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "5" , "-b", "0.0.0.0:5000", "Classification_API:app"]
