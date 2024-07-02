from flytekit import task
from prometheus_api_client import PrometheusConnect
import os

from .fetch import get_pod_template

# Get system ip from container environment variable set with pyflyte --env SYSTEM_IP=xxx
SYSTEM_IP = os.environ.get('SYSTEM_IP')

@task(pod_template=get_pod_template())
def trigger_retraining() -> bool:
    prom = PrometheusConnect(url=f"http://{SYSTEM_IP}:30002/", disable_ssl=True)
    if (int(prom.custom_query(query="sum(ray_serve_deployment_replica_healthy{})")[0]["value"][1]) < 9):
        return True
    else:
        return False
