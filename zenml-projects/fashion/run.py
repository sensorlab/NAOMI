from zenml import pipeline, ExternalArtifact
from zenml.config import DockerSettings
from steps import train, deploy, eval, fetch_data, retrain
from zenml.integrations.kubernetes.flavors.kubernetes_orchestrator_flavor import KubernetesOrchestratorSettings
import os
import argparse

kubernetes_settings = KubernetesOrchestratorSettings(
    pod_settings={
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "kubernetes.io/arch",
                                    "operator": "In",
                                    "values": ["amd64"],
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
)

script_dir = os.path.dirname(os.path.abspath(__file__))
requirements_path = os.path.join(script_dir, 'requirements.txt')
docker_settings = DockerSettings(requirements=requirements_path)
# docker_settings = DockerSettings(parent_image="localhost:32000/zenml:ray_pipe-orchestrator")


@pipeline(enable_cache=False, settings={"docker": docker_settings, "orchestrator.kubernetes": kubernetes_settings})
def fashion():
    deploy.after(eval)  # so evaluation is first in the pipeline
    eval.after(train)
    data = fetch_data()
    model_uri = train(train_images=data[0], train_lables=data[1])
    eval(model_uri=model_uri, test_images=data[2], test_lables=data[3])
    deploy(model_uri)


@pipeline(enable_cache=False, settings={"docker": docker_settings, "orchestrator.kubernetes": kubernetes_settings})
def fashion_retrain():
    deploy.after(eval)  # so evaluation is first in the pipeline
    eval.after(retrain)
    data = fetch_data()
    model_uri = retrain(train_images=data[0], train_lables=data[1], model=ExternalArtifact(name="Fashion model"))
    eval(model_uri=model_uri, test_images=data[2], test_lables=data[3])
    deploy(model_uri)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Choose the pipeline to run")
    parser.add_argument('--retrain', action='store_true')
    args = parser.parse_args()

    fashion_retrain() if args.retrain else fashion()
