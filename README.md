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
$ gcloud run deploy scrape-svc-euw1 --image scrape-svc --region europe-west1 --concurrency 4 --platform managed --allow-unauthenticated --cpu 2 --memory 1Gi  
```

## Unit Test
```
$ curl -H "Content-type: application/json" -H "Authorization: Bearer $(gcloud auth print-identity-token)" -X POST https://scrape-svc-<service-URL>.a.run.app/stroccurences -d '{"query":"ôtés Produits de la culture et de l'\''elevage"}' 
```

