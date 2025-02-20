FROM python:3.12-slim

RUN apt-get update && apt-get install -y openjdk-17-jdk make vim bash-completion && \
	rm -rf /var/lib/apt/lists/*
RUN java -version

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV PYSPARK_PYTHON=/app/venv/bin/python

WORKDIR /app

COPY . /app
RUN chmod -R 755 /app

EXPOSE 8080

RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install -r requirements.txt
RUN chmod -R +x /app
RUN echo "source /etc/profile.d/bash_completion.sh" >> ~/.bashrc

# CMD tail -f /dev/null
CMD ["make", "run"]
