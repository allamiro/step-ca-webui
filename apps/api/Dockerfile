FROM python:3.12-slim

RUN useradd -m -u 10001 appuser

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY app /app/app
RUN python -m venv /home/appuser/venv && chown -R appuser:appuser /home/appuser/venv /app

USER appuser
ENV PATH="/home/appuser/venv/bin:${PATH}"
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
