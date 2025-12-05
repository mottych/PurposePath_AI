FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY coaching/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code with proper module structure
# NOTE: Explicitly exclude coaching/shared (deprecated - use root shared/ instead)
COPY coaching/src ${LAMBDA_TASK_ROOT}/coaching/src
COPY coaching/prompts ${LAMBDA_TASK_ROOT}/coaching/prompts
COPY coaching/__init__.py ${LAMBDA_TASK_ROOT}/coaching/__init__.py
COPY shared ${LAMBDA_TASK_ROOT}/shared

# Use handler with proper module path
CMD ["coaching.src.api.main.handler"]

