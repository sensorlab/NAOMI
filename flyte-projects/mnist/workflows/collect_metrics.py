from flytekit import task, PodTemplate
from kubernetes.client import V1PodSpec, V1Container, V1ResourceRequirements
from prometheus_api_client import PrometheusConnect

@task(pod_template=PodTemplate(
    pod_spec=V1PodSpec(
        node_selector={
            "kubernetes.io/arch": "amd64"
        },
        containers=[
            V1Container(
                name="primary",
                resources=V1ResourceRequirements(
                    limits={
                        "memory": "2Gi",
                        "cpu": "1000m"
                    },
                    requests={
                        "memory": "1Gi"
                    }
                ),
            ),
        ],
    )
)
)
def trigger_retraining() -> bool:
    prom = PrometheusConnect(url="http://193.2.205.27:30002/", disable_ssl=True)
    if (int(prom.custom_query(query="sum(ray_serve_deployment_replica_healthy{})")[0]["value"][1]) < 9):
        return True
    else:
        return False
