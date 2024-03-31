FROM python:3-slim

# Set the timezone to Asia/Singapore
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Singapore
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime
RUN echo $TZ > /etc/timezone

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./notification.py .
CMD [ "python", "./notification.py" ]
