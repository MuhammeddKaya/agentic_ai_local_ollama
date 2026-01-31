FROM python:3.11-slim

RUN useradd -m agentuser
WORKDIR /app

COPY agent.py /app/agent.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /sandbox && chown -R agentuser:agentuser /sandbox

USER agentuser

ENV PYTHONUNBUFFERED=1


