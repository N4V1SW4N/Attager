FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/delivery_agent_plus/ ./agents/delivery_agent_plus/

EXPOSE 10005

CMD ["python", "-m", "agents.delivery_agent_plus", "--host", "0.0.0.0", "--port", "10005"]
