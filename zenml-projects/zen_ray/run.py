from zenml import pipeline
from zenml.config import DockerSettings
from steps import train, deploy, eval, fetch_data, test_deploy

docker_settings = DockerSettings(requirements="requirements.txt")

@pipeline(enable_cache=False, settings={"docker": docker_settings})
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
    cron_expression = "37 * * * *"
    schedule = Schedule(cron_expression=cron_expression)
    ray_pipe = ray_pipe.with_options(schedule=schedule)
    """

    ray_pipe()
