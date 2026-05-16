FROM prefecthq/prefect:3-latest

# copy requirements and install
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /flows

# default: bootstrap the pool if needed, then start a worker that mounts /flows so it can run flows/deploy.py and execute flows
CMD ["bash","-lc","prefect work-pool create local-pool --type process || true; prefect worker start --pool local-pool --name local-worker"]
