# TODO seperate docker files for both architecures, requirements and script for building images, maybe github ci/cd
# Start from the rayproject/ray:2.6.3-aarch64 image for raspberry pi

FROM rayproject/ray:2.9.1-py310

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt
