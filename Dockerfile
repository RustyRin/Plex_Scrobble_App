FROM python

ADD main.py .
ADD requirements.txt .

RUN pip install requests
RUN pip install -r requirements.txt

CMD ["python", "./main.py"]