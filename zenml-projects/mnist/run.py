from zenml import pipeline
from zenml.config import DockerSettings
from steps import train, deploy, eval, fetch_data, test_deploy
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
def ray_pipe():
    deploy.after(eval)  # so evaluation is first in the pipeline
    test_deploy.after(deploy)
    eval.after(train)

    data = fetch_data()
    model_uri = train(x_train=data[0], y_train=data[1])
    eval(model_uri=model_uri, x_test=data[2], y_test=data[3])
    deploy(model_uri)
    test_deploy()


if __name__ == "__main__":
    """
    # For scheduled runs use Cron:
    # cron_expression = "*/30 * * * *" # for repeated run
    cron_expression = "35 * * * *" # run at <any hour>:35m
    schedule = Schedule(cron_expression=cron_expression)
    ray_pipe = ray_pipe.with_options(schedule=schedule)
    """
    # Cleanup
    try:
        Client().delete_pipeline("ray_pipe")
    except KeyError as e:
        print("Can't delete pipeline that doesn't exist, proceeding...")

    os.system("zenml artifact prune -y")
    ray_pipe()
