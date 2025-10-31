FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code directly to task root
COPY src ${LAMBDA_TASK_ROOT}/src
COPY shared ${LAMBDA_TASK_ROOT}/shared

# Create main handler that imports from src.api.main
RUN echo 'from src.api.main import handler' > ${LAMBDA_TASK_ROOT}/lambda_handler.py && \
    echo '__all__ = ["handler"]' >> ${LAMBDA_TASK_ROOT}/lambda_handler.py

# Use handler
CMD ["lambda_handler.handler"]

