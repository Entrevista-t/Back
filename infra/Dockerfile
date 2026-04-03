ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS runtime

WORKDIR /app
COPY requirements-api.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements-api.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM ${BASE_IMAGE} AS dev

WORKDIR /app
COPY requirements-api.txt requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements-api.txt -r requirements-dev.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]