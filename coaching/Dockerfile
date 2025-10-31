FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code with correct structure
COPY src ${LAMBDA_TASK_ROOT}/coaching/src
COPY shared ${LAMBDA_TASK_ROOT}/shared

# Create __init__.py for coaching package
RUN touch ${LAMBDA_TASK_ROOT}/coaching/__init__.py

# Copy bootstrap handler
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Use bootstrap handler that sets up Python path
CMD ["lambda_handler.handler"]

