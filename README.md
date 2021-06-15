# search-requests

## Build the scrape-svc container image
From Cloud Shell: 
```
$ gcloud config set project <project-name>  
$ cd <repo_dir>/scrape-svc  
$ gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/scrape-svc  
```

## Create the BigQuery table
From Cloud Shell:
```
$ bq --location=europe-west1 mk --dataset $GOOGLE_CLOUD_PROJECT:meae_dataset
$ bq mk meae_dataset.meae_wsreqs_table
```

## Setup up the BigQuery table access rights
From GCP UI, in the IAM menu, give the Compute Service Account the BigQuery data Editor role.
This can also be done from Cloud Shell
```
$ gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member=serviceAccount:<project-ID>-compute@developer.gserviceaccount.com --role=roles/bigquery.dataEditor
```
(the project id in the Servica account name can be found in the UI).

## Define the BQ table schema
In the UI, create the following schema for the BigQuery Table :
- lexique : String : Nullable
- categorie : String : Nullable
- res : Integer : Nullable

# Test with only one Cloud Run service

## Start the Cloud Run service
```
$ gcloud run deploy scrape-svc-euw1 --image gcr.io/$GOOGLE_CLOUD_PROJECT/scrape-svc --region europe-west1 --concurrency 4 --platform managed --allow-unauthenticated --cpu 2 --memory 1Gi --max-instances 300 
```

## Unit Test
```
$ curl -H "Content-type: application/json" -H "Authorization: Bearer $(gcloud auth print-identity-token)" -X POST https://scrape-svc-<service-URL>.a.run.app/stroccurences -d '{"query":"ôtés Produits de la culture et de l'\''elevage", "lexique": "ôtés", "categorie": "Produits de la culture et de l'\''elevage"}' 
```

## Install the Cloud Tasks module
Preferably from a Notebook/instance (vs Cloud Shell which will loose the change):
```
$ pip install google-cloud-tasks==2.2.0
```

## Create a Cloud Tasks queue
From Cloud Shell:
```
$ gcloud tasks queues create wsreqs-euw1 --max-dispatches-per-second=80 --max-concurrent-dispatches=500
```

## Run the tasks filling program
From a Notebook/instance (in the same directory as the 'requetes.txt' file):
```
$ python3 launch-tasks.py
```

# Use multiple concurrent Cloud Run services

## Deploy the Cloud Run services
From Cloud Shell:
```
$ for region in `cat regions-list.txt`; do echo $(gcloud run deploy scrape-svc-$region --region $region --image gcr.io/$GOOGLE_CLOUD_PROJECT/scrape-svc --platform managed --no-allow-unauthenticated --concurrency 4 --cpu 2 --memory 1Gi --max-instances 300 --format 'value(status.url)') >> urls-list.txt; done
```

## Create the Cloud Tasks queues
From Cloud Shell:
```
$ for region in `cat regions-list.txt`; do gcloud tasks queues create wsreqs-queue-$region --log-sampling-ratio=1.0 --max-attempts=100 --max-concurrent-dispatches=500 --max-dispatches-per-second=50 ; done
```

## Split the input file
The complete list of requests must be prepared in a CSV file with the following format :
```
mot-lexique;categorie
```
From a Vertex AI Notebook (for more simplicity), open a terminal and upload the 'regions-list.txt' file, the 'urls-list.txt' file, and your input CSV file with all the queries.
Then, split the input file into 9 pieces:
```
$ split -n l/9 allreqs-quoted.csv 
```
you now thave 9 files - xaa to xai - that contain approximately equals numbers of lines.

## Launch the requests to the queues
From your Vertex AI Notebook, create and launch 9 copies - 1 per target region - of the 'Tasks-Launcher-4-0.ipynb' Notebook, and change only the file name and the region index - 0 to 8 - in the last cell of the notebook.
Execute all the notebook cells in sequence.

# Export the results to a csv file
From the BigQuery menu in the UI, run the following SQL script to sort the results
```
SELECT *
FROM `test-meae.meae_dataset.meae_wsreqs_table`
ORDER BY lexique, categorie
```
Then downlaod the result to a file using the export menu.
