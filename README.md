 # Medical <img src="https://github.com/CogStack/MedCATtrainer/blob/master/webapp/frontend/src/assets/cat-logo.png" width=45>oncept Annotation Tool Trainer
 
MedCATTrainer is an interface for building, improving and customising a given Named Entity Recognition and Linking (NER+L) model for biomedical domain text

MedCATTrainer was presented at EMNLP/IJCNLP 2019 :tada:
[here](https://www.aclweb.org/anthology/D19-3024.pdf) 

## Developer Guide
 
1\. Clone the repo:

`$ git clone https://github.com/CogStack/MedCATtrainer.git`

2\.  Build and run the docker image

`$ cd MedCATTrainer`

`$ docker-compose -f docker-compose-dev.yml build`

If the build fails with an error code 137, the virtual machine running the docker 
daemon does not have enough memory. Adjust in docker daemon settings CLI or associated docker GUI.

`$ docker-compose -f docker-compose-dev.yml up`

3\. MedCATTrainer is now running:
- The app is at http://localhost:8001/
- The administrator (admin) app is at http://localhost:8001/admin/

A username / password permissions the data / models that are setup via the administrator app. 
An initial super user must be setup to login to login to admin. 

### Administrator Setup

1\.  The container runs a vanilla [django](https://www.djangoproject.com/) app, 
that by default has no users (or super users). To add the first superuser use the django manage.py 
createsuperuser function within the runnning container. **Further users, (i.e. annotators for 
a given project) can be added via the django admin UI.**

 &nbsp;&nbsp;1\. First get the running container name:
`$ docker ps`

> CONTAINER ID        IMAGE                      COMMAND                  CREATED             STATUS              PORTS                            NAMES
> 62b9a2380f30        medcattrainer_nginx           "nginx -g 'daemon of…"   2 days ago          Up 2 days           80/tcp, 0.0.0.0:8001->8000/tcp   medcattrainer_nginx_1
> 93168cc98c15        medcattrainer_medcattrainer   "/home/run.sh"           2 days ago          Up 2 days           8000/tcp                         **medcattrainer_medcattrainer_1**

&nbsp;&nbsp;2\. Login to the container running django. (The 2nd entry of the output of the ps, as indicated in **bold**).

`docker exec -it cattrainer_medcattrainer_1 bash`

> root@93168cc98c15:/home/api# 

&nbsp;&nbsp;3\. Create the superuser username and password by following the prompts.

`root@93168cc98c15:/home/api# python manage.py createsuperuser`

> Username (leave blank to use 'root'): 
> Email address: 
> Password: 
> Password (again): 
> The password is too similar to the username.
> This password is too short. It must contain at least 8 characters.
> This password is too common.
> Bypass password validation and create user anyway? [y/N]: y
> Superuser created successfully.

&nbsp;&nbsp;4\. You can now login to the main and admin app with the newly created user.

&nbsp;&nbsp;5\. To upload documents and begin annotating, you'll first need to create a project via the admin page: 
http://localhost:8001/admin/.

### Create an Annotation Project

Using the admin page, a configured superuser can create, edit and delete annotation projects. 

1\. On http://localhost:8001/admin/, choose 'Project annotate entities'.

2\. 'Add Project Annotate Entities'

3\. Complete the form as indicated

4\. '+' next to fields allows the addition of those field types in pop out windows

5\. Datasets can be uploaded in CSV format. Example:

| name  | text                   | 
|-------|------------------------|
| Doc 1 | Example document text  |
| Doc 2 | More example text      |

The name column is optional, and will be auto-generated for each document if not supplied in the upload.

6\. CUIs (UMLS Concept Unique Identifiers) and TUIs (UMLS Term Unique Identifiers), allow projects to be
configured to only display a subset of total UMLS concepts. They can be specified in a comma separated
list. For example: T184, T047.

7\. Example Concept and Vocab databses are freely available on MedCAT [github](https://github.com/CogStack/MedCAT).
Note. UMLS is not freely available, so only these smaller trained concept / vocab databases are made available currently.


8\. Tasks allow for the creation of meta-annotations and their associated set of values an annotator can use.
An example 'meta-annotation' could be 'Temporality'. Values could then be 'Past', 'Present', 'Future'.


A more comprehensive guide for setting up a project, will be made available soon.


### Annotation Guidelines

Annotation guidelines can assit guiding annotators when annotatinng texts for a MedCATTrainer project.
 
Once an initial guideline has been defined, a pilot project in MedCATTrainer can be used to further 
refine the guideline also.









