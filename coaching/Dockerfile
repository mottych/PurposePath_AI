FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code directly to task root  
COPY src ${LAMBDA_TASK_ROOT}/src
COPY shared ${LAMBDA_TASK_ROOT}/shared

# Use handler directly from main.py
CMD ["src.api.main.handler"]

