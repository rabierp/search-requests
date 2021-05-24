# search-requests

## Build the scrape-svc container image
From Cloud Shell: 
```
$ gcloud config set project <project-name>  
$ cd <repo_dir>/scrape-svc  
$ gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/scrape-svc  
```

## Start the Cloud Run service
```
$ gcloud run deploy scrape-svc-euw1 --image gcr.io/$GOOGLE_CLOUD_PROJECT/scrape-svc --region europe-west1 --concurrency 4 --platform managed --allow-unauthenticated --cpu 2 --memory 1Gi --max-instances 300 
```

## Unit Test
```
$ curl -H "Content-type: application/json" -H "Authorization: Bearer $(gcloud auth print-identity-token)" -X POST https://scrape-svc-<service-URL>.a.run.app/stroccurences -d '{"query":"ôtés Produits de la culture et de l'\''elevage"}' 
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

# Deploy the Cloud Run Services
From Cloud Shell:
```
$ for region in `cat regions-list.txt`; do echo $(gcloud run deploy scrape-svc-$region --region $region --image gcr.io/pascal-sandbox/my_scrapping_service --platform managed --no-allow-unauthenticated --format 'value(status.url)') >> urls-list.txt; done
```
