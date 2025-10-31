FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire coaching package
WORKDIR /var/task
COPY . /tmp/coaching_build/

# Install coaching package
RUN cd /tmp/coaching_build && \
    pip install --no-cache-dir --no-deps -e . && \
    cd /var/task

# Copy shared module
COPY shared ./shared

# Set the Lambda handler
CMD ["coaching.src.api.main.handler"]

