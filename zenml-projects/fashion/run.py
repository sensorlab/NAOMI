from zenml import pipeline
from zenml.config import DockerSettings
from steps import train, deploy, eval, fetch_data
from zenml.integrations.kubernetes.flavors.kubernetes_orchestrator_flavor import KubernetesOrchestratorSettings
from zenml.client import Client
import os

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


if __name__ == "__main__":
    """
    # For scheduled runs use Cron:
    # cron_expression = "*/30 * * * *" # for repeated run
    cron_expression = "37 * * * *"
    schedule = Schedule(cron_expression=cron_expression)
    ray_pipe = ray_pipe.with_options(schedule=schedule)
    """
    try:
        Client().delete_pipeline("fashion")
    except KeyError as e:
        print("Can't delete pipeline that doesn't exist, proceeding...")

    os.system("zenml artifact prune -y")
    fashion()
