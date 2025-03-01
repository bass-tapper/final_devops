# Rick & Morty API Application

A RESTful API that fetches and serves character information from the [Rick & Morty API](https://rickandmortyapi.com/). This application allows you to query characters from the Rick & Morty universe.

## Features

- Get all characters with pagination
- Get specific character by ID
- Containerized for easy deployment
- Kubernetes and Helm support
- CI/CD pipeline with GitHub Actions

## Running Locally

### Prerequisites

- Python 3.9+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rick-morty-api.git
   cd rick-morty-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python rick-morty-api.py
   ```

4. The API will be available at `http://localhost:5000`

## Docker Deployment

### Prerequisites

- Docker

### Building and Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t rick-morty-api:latest .
   ```

2. Run the Docker container:
   ```bash
   docker run -p 5000:5000 --name rick-morty-api rick-morty-api:latest
   ```

3. The API will be available at `http://localhost:5000`

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured to connect to your cluster

### Deploying with kubectl

1. Apply the Kubernetes manifests:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   kubectl apply -f ingress.yaml
   ```

2. Check the deployment status:
   ```bash
   kubectl get pods -l app=rick-morty-api
   kubectl get services -l app=rick-morty-api
   kubectl get ingress
   ```

3. The API will be available at the ingress address (typically configured with a domain name)

## Helm Deployment

### Prerequisites

- Helm 3.x
- Kubernetes cluster
- kubectl configured to connect to your cluster

### Installing with Helm

1. Install the Helm chart:
   ```bash
   helm install rick-morty-api ./helm/rick-morty-api
   ```

2. For custom configuration, you can use values:
   ```bash
   helm install rick-morty-api ./helm/rick-morty-api --set replicaCount=3 --set service.type=NodePort
   ```

3. Verify the installation:
   ```bash
   helm list
   kubectl get pods -l app.kubernetes.io/name=rick-morty-api
   ```

### Upgrading with Helm

```bash
helm upgrade rick-morty-api ./helm/rick-morty-api
```

### Uninstalling with Helm

```bash
helm uninstall rick-morty-api
```

## API Endpoints

### Health Check

```
GET /health
```

Returns status 200 if the application is running correctly.

### Get All Characters

```
GET /characters
```

Optional query parameters:
- `page`: Page number (default: 1)

Response:
```json
{
  "characters": [
    {
      "id": 1,
      "name": "Rick Sanchez",
      "status": "Alive",
      "species": "Human",
      "type": "",
      "gender": "Male"
    },
    ...
  ],
  "info": {
    "count": 671,
    "pages": 34,
    "next": "http://localhost:5000/characters?page=2",
    "prev": null
  }
}
```

### Get Character by ID

```
GET /characters/{id}
```

Response:
```json
{
  "id": 1,
  "name": "Rick Sanchez",
  "status": "Alive",
  "species": "Human",
  "type": "",
  "gender": "Male",
  "origin": {
    "name": "Earth (C-137)",
    "url": "https://rickandmortyapi.com/api/location/1"
  },
  "location": {
    "name": "Citadel of Ricks",
    "url": "https://rickandmortyapi.com/api/location/3"
  },
  "image": "https://rickandmortyapi.com/api/character/avatar/1.jpeg",
  "episode": [
    "https://rickandmortyapi.com/api/episode/1",
    "https://rickandmortyapi.com/api/episode/2",
    ...
  ],
  "url": "https://rickandmortyapi.com/api/character/1",
  "created": "2017-11-04T18:48:46.250Z"
}
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and continuous deployment.

### Workflow Stages

1. **Build**: Builds the Docker image and tags it with the git SHA and 'latest'
2. **Test**: Runs tests on the Python application
3. **Push**: Pushes the Docker image to the container registry
4. **Deploy**: Deploys to Kubernetes using Helm

### Environment Variables and Secrets

The CI/CD pipeline uses the following secrets:
- `DOCKER_USERNAME`: Username for the Docker registry
- `DOCKER_PASSWORD`: Password for the Docker registry
- `KUBECONFIG`: Kubernetes configuration for deployment

### How to Configure

The workflow is defined in `.github/workflows/ci-cd.yaml`. You can customize it by:

1. Updating the Docker registry information
2. Modifying the test commands
3. Changing the deployment environment

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab by clicking "Run workflow".

<<<<<<< HEAD
# final_devops
The final DevOps test
=======
# Rick & Morty API Project

## Setup and Usage

### 1. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Required Packages
```bash
pip install requests
```

### 3. Run API Script
```bash
python rick-morty-api.py
```

### 4. Verify Output
- Successful execution creates `rick_morty_characters.csv`
- Check first 5 entries:
```bash
head -n5 rick_morty_characters.csv
```

### 5. Deactivate Virtual Environment
```bash
deactivate
```

> **Note**  
> Reactivate with `source venv/bin/activate` for future sessions

### 6. Deploy to Kubernetes
```bash
# Apply the Kubernetes manifests
kubectl apply -f yamls/Deployment.yaml
kubectl apply -f yamls/Service.yaml
kubectl apply -f yamls/Ingress.yaml

# Verify the deployment
kubectl get pods
kubectl get services
kubectl get ingress
```

### 7. Access the Application
- Update your `/etc/hosts` file to include:
```
127.0.0.1 rick-morty-api.example.com
```
- Access the application at `http://rick-morty-api.example.com`

### 8. Deploy Using Helm
```bash
# Install the Helm chart
helm install rick-morty-api ./helm

# Verify the deployment
kubectl get pods
kubectl get services
kubectl get ingress
```

### 9. Customize Deployment
To customize the deployment, edit the `values.yaml` file in the `helm` directory and then upgrade the Helm release:
```bash
helm upgrade rick-morty-api ./helm
```

### 10. Clean Up
```bash
# Delete the Helm release
helm uninstall rick-morty-api

# Alternatively, delete the Kubernetes resources directly
kubectl delete -f yamls/Deployment.yaml
kubectl delete -f yamls/Service.yaml
kubectl delete -f yamls/Ingress.yaml
```
>>>>>>> a8cde2b (Initial commit)
