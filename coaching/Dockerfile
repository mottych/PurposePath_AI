FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY src ./src
COPY shared ./shared

# Set the Lambda handler
# Uses main_v2.py with Phase 7 architecture (new routes, middleware, auth)
CMD ["src.api.main_v2.handler"]

