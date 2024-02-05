# TODO seperate docker files for both architecures, requirements and script for building images, maybe github ci/cd
# Start from the rayproject/ray:2.6.3-aarch64 image for raspberry pi

FROM rayproject/ray:2.9.1-py310

RUN pip install torch torchvision pillow requests starlette evaluate transformers fastapi
RUN pip install mlflow keras tensorflow
RUN pip install fastapi python-multipart
RUN pip install ray[rllib]
