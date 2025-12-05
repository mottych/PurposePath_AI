FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY coaching/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code with proper module structure
# coaching/src -> coaching/src (maintains import paths like coaching.src.api.main)
COPY coaching ${LAMBDA_TASK_ROOT}/coaching
COPY coaching/shared ${LAMBDA_TASK_ROOT}/shared

# Use handler with proper module path
CMD ["coaching.src.api.main.handler"]

