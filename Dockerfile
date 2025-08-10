FROM public.ecr.aws/lambda/python:3.11
WORKDIR ${LAMBDA_TASK_ROOT}

COPY Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY app/ ${LAMBDA_TASK_ROOT}/app
COPY lambda_handlers/ ${LAMBDA_TASK_ROOT}/lambda_handlers/

# API Lambda entrypoint (worker will override via Terraform image_config.command)
CMD ["app.main.handler"]