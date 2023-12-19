from zenml import pipeline, ExternalArtifact
from zenml.config import DockerSettings
from steps import train, deploy, eval, fetch_data, test_deploy, retrain
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
        },
        "resources": {
            "limits": {
                "cpu": "1000m",
                "memory": "2Gi"
            },
            "requests": {
                "memory": "1Gi",
                "cpu": "1000m"
            }
        }
    }
)

script_dir = os.path.dirname(os.path.abspath(__file__))
requirements_path = os.path.join(script_dir, 'requirements.txt')
docker_settings = DockerSettings(requirements=requirements_path)
# docker_settings = DockerSettings(parent_image="localhost:32000/zenml:ray_pipe-orchestrator")

@pipeline(enable_cache=False, settings={"docker": docker_settings, "orchestrator.kubernetes": kubernetes_settings})
def mnist_train():
    # deploy.after(eval)  # so evaluation is first in the pipeline
    test_deploy.after(deploy)
    eval.after(train)

    data = fetch_data()
    model_uri = train(x_train=data[0], y_train=data[1])
    eval(model_uri=model_uri, x_test=data[2], y_test=data[3])
    deploy(model_uri)
    test_deploy()


@pipeline(enable_cache=False, settings={"docker": docker_settings, "orchestrator.kubernetes": kubernetes_settings})
def mnist_retraining():
    # deploy.after(eval)
    test_deploy.after(deploy)
    eval.after(retrain)

    data = fetch_data()
    model = retrain(x_train=data[0], y_train=data[1], model=ExternalArtifact(name="mnist_model"))
    eval(model_uri=model, x_test=data[2], y_test=data[3])
    deploy(model)
    test_deploy()


if __name__ == "__main__":
    """
    # For scheduled runs use Cron:
    # cron_expression = "*/30 * * * *" # for repeated run
    cron_expression = "35 * * * *" # run at <any hour>:35m
    schedule = Schedule(cron_expression=cron_expression)
    ray_pipe = ray_pipe.with_options(schedule=schedule)
    """
    parser = argparse.ArgumentParser(description="Choose the pipeline to run")
    parser.add_argument('--retrain', action='store_true')
    args = parser.parse_args()

    if args.retrain:
        mnist_retraining()
    else:
        mnist_train()
