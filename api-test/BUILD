poetry_requirements(
    name="poetry",
)

pex_binary(
    name="api-test",
    dependencies=["api-test/api_test/main.py","api-test:poetry#uvicorn","api-test:poetry#psycopg" ],
    execution_mode="venv",
    script="uvicorn"
)

docker_image(
    name="api-test-docker",
)
