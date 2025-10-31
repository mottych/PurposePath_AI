FROM public.ecr.aws/lambda/python:3.11

# Install system deps if needed

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code - preserve directory structure for imports
COPY src ./coaching/src
COPY shared ./shared

# Create __init__.py for coaching package
RUN touch ./coaching/__init__.py

# Set the Lambda handler
# Uses main.py with Phase 7 architecture (new routes, middleware, auth)
CMD ["coaching.src.api.main.handler"]

