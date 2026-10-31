# SPDX-License-Identifier: Apache-2.0
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY services/api/ /app/
COPY eval/ /app/eval/
RUN python -m pip install --upgrade pip && python -m pip install .

EXPOSE 8000
CMD ["uvicorn", "container_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
