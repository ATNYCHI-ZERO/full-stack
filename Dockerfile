FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir cryptography numpy scikit-learn shap pandas
CMD ["python", "demo.py"]
