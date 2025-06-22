FROM public.ecr.aws/lambda/python:3.11

# Set working directory inside Lambda container
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install dependencies into Lambda's task root
COPY Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy app code into the container (entire app folder)
COPY app/ ${LAMBDA_TASK_ROOT}/app

# Set the command to run the FastAPI app inside app/main.py
CMD ["app.main.handler"]

