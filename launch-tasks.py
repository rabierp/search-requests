from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import json

# Create a client.
tasks_client = tasks_v2.CloudTasksClient()

# TODO(developer): Uncomment these lines and replace with your values.
project = '--GCP PROJECT--'
queue = '--QUEUE NAME--'
location = 'europe-west1'
url = 'https://--INSERT THE Cloud RUn Service URL--.a.run.app/stroccurences'

# Construct the fully qualified queue name.
parent = tasks_client.queue_path(project, location, queue)

def transfo_line(line):
    list = line[1:-2].replace('" + "', ' ').replace(',', '').split(' ')
    return " ".join(list)
  
# Construct the request body.
def build_request(payload):
    task = {
        "view": tasks_v2.types.Task.View.FULL,
        "http_request": {  # Specify the type of request.
            "url": url,  # The full url path that the task will be sent to.
            # not required because Cloud Run unauthenticate request are accepted :
            #"oidc_token": {"service_account_email": "sevice-account@gcp-project.iam.gserviceaccount.com", "audience": "https://--Cloud Run Service URL--/stroccurences"},
        }
    }
    if payload is not None:
        if isinstance(payload, dict):
            # Convert dict to JSON string
            payload = json.dumps(payload)
            # specify http content-type to application/json
            task["http_request"]["headers"] = {"Content-type": "application/json"}

        # The API expects a payload of type bytes.
        converted_payload = payload.encode()

        # Add the payload to the request.
        task["http_request"]["body"] = converted_payload

    return task

with open("./requetes.uniq.all.txt") as file:
    line = file.readline()
    nb = 1
    while line:
        search = transfo_line(line)
        task = build_request({'query':search})
        response = tasks_client.create_task(request={"parent": parent, "task": task})
        if nb % 10000 == 0:
            print(str(nb) + " ")
        line = file.readline()
        nb = nb + 1
