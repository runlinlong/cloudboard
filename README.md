# Cloudboard

Cloudboard is a small task management application built for the PA2577 Applied Cloud Computing and Big Data course.

Users can create tasks, choose a priority, move tasks between To do, In progress and Done, and view completion statistics in a browser.

## Architecture

The application contains two Python microservices and a PostgreSQL database:

- **Dashboard** provides the web interface and calls the Tasks REST API.
- **Tasks** provides the task REST API and reads and writes task data.
- **PostgreSQL** stores the tasks and uses persistent Kubernetes storage.

Request flow:

```text
Browser -> Dashboard -> Tasks -> PostgreSQL
```

Dashboard and Tasks use separate Kubernetes Deployments and can be scaled independently.

## Docker images

- Dashboard: <https://hub.docker.com/r/runlinlong/cloudboard-dashboard>
- Tasks: <https://hub.docker.com/r/runlinlong/cloudboard-tasks>

Both images use the `v1` tag.

## Run with Kubernetes

Requirements:

- Docker Desktop
- Kubernetes command line tool (`kubectl`)
- kind
- Windows PowerShell

From the project directory, run:

```powershell
.\scripts\init-local.ps1
.\scripts\create-cluster.ps1
.\scripts\deploy.ps1 -DockerHubUser runlinlong -Tag v1
```

Open the application in a browser:

<http://127.0.0.1:18081>

Check the running components:

```powershell
$k = @('--kubeconfig', '.local/kubeconfig', '--context', 'kind-cloudboard-coursework', '-n', 'cloudboard')
kubectl @k get deployments,pods,services,pvc
```

## REST API

The main endpoints are:

- `GET /api/tasks` - list tasks
- `POST /api/tasks` - create a task
- `PATCH /api/tasks/{id}` - update a task status
- `DELETE /api/tasks/{id}` - delete a task
- `GET /api/dashboard` - return tasks and summary information

The browser calls Dashboard, and Dashboard programmatically calls the Tasks REST API.

## Kubernetes configuration

The deployment configuration is in [`k8s/app.yaml`](k8s/app.yaml). It defines the two application Deployments, their Services, PostgreSQL, the persistent volume claim and the Dashboard NodePort.

PostgreSQL uses one replica. Dashboard and Tasks use two replicas each. The database password is provided through a Kubernetes Secret.

## Project structure

```text
services/dashboard   Dashboard service and web interface
services/tasks       Tasks REST API
k8s                  Kubernetes YAML files
scripts              PowerShell deployment scripts
tests                API tests
```

This is a local course demonstration. It does not include user login or HTTPS. A production version would require authentication, access control and database backups.
