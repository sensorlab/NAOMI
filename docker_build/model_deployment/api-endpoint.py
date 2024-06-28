from typing import List
from fastapi import FastAPI
import os
import mlflow

# Add your own imports and functions here

app = FastAPI()

# SEMR's model store endpoint, CHANGE THIS TO YOUR OWN IP
os.environ['MLFLOW_TRACKING_URI'] = 'http://<SEMR_IP>:31007'

# Read the model version from the os variable (Defined in the helm charts)
model_version = os.getenv('MODEL_VERSION', "latest")

# Modify the model_uri to point to the correct model name
model_uri = f"models:/<model_name>/{model_version}"

# Modify the MLflow loading function https://mlflow.org/docs/2.10.2/index.html
model = mlflow.pytorch.load_model(model_uri)
model.eval()
print("Model loaded!")

@app.post("/")
async def echo(data: List[List[List[float]]]):
    # Data transformations
    # tensor_data = torch.tensor(data)
    # tensor_data = tensor_data.unsqueeze(0)

    # Inference
    # cnn_labels_array = cnn_predict(tensor_data, model)
    # counts = Counter(cnn_labels_array)

    return {"prediction": str(counts)}

