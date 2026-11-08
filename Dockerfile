FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN grep -vi '^torch' requirements.txt > req.txt \
    && pip install --no-cache-dir --no-deps torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir filelock typing_extensions sympy networkx jinja2 fsspec \
    && pip install --no-cache-dir -r req.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
COPY backend ./backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "api:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
