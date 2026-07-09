FROM python:3.13-alpine

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
