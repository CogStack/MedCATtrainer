This repo provides a simple interface to inspect, improve and add concepts to biomedical NER+L model (e.g. MedCAT) and a further interface for research specific training data collection.

### How to use: the basic example with concepts from MedMentions
1. Clone this repository

2. Build `docker-compose build `

3. Run `docker-compose up -d`

4. You are now able to access the web service on `<your_ip>:8001`


### The API
Once the container is running the API is available at `<your_ip>:8001/api`.


Request JSON: (you only need to set the 'text' field the rest can be left blank)
```
{
    "content": {
        "text": "",
        "metadata:": {},
    },
    "applicationParams": {},
    "footer": {}
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


Video: [Medcat Trainer](https://youtu.be/lM914DQjvSo) 
