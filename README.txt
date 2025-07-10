Scripts to fetch (currently only from JJit) and assess using Openai api key job offers written in Python
Run fetch job script
`python fetch_jobs.py --category pm --location remote --keyword "Product Owner"`
Run score jobs script
`python score_offers.py --input job_offers_pm_remote.csv --cv cv.txt --output scored_job_offers.csv`
as it can be seen from the commands the output is CSV and CV needs to be input as text extracted
