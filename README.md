This repo provides a simple interface to inspect, improve and add concepts to biomedical NER+L model (e.g. MedCAT) and a further interface for research specific training data collection.

### How to use (e.g. for the CT example)
1. Clone this repository

2. Move the pretrained models into the `medcatweb/webapp/models/` Keep the model names in their original form (`vocab.dat` and `cdb.dat`)

3. Build `docker-compose -f docker-compose-ct.yml build`

4. Run `docker-compose -f docker-compose-ct.yml up -d`

5. You are now able to access the web service on `<your_ip>:8001`


### The API
Once the container is running the API is available at `<your_ip>:8001/api`.


Request JSON: (you only need to set the 'text' field the rest can be left blank)
```
{
    "content": {
        "text": "",
        "metadata:": {},
        "footer": {}
    },
    "applicationParams": {}
}
```



Response JSON:
```
{
    "result": {
        "text: "",
        "annotations": [],
        "metadata": {},
        "success": True / False,
        "errors": [],
        "footer": {}
    }
}
```
