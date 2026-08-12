FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY app ./app
COPY run.py ./run.py

RUN addgroup --system farmda \
    && adduser --system --ingroup farmda --home /app farmda \
    && chown -R farmda:farmda /app

USER farmda

EXPOSE 5000

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=8", "--channel-timeout=30", "--max-request-body-size=1048576", "--ident=Farmda", "run:app"]
