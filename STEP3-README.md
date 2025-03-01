# Step 3: Kubernetes Deployment

## Prerequisites
Before proceeding with the Kubernetes deployment, ensure you have the following installed and configured:
- **kubectl**: Kubernetes command-line tool
- **Minikube**: Local Kubernetes cluster
- **Docker**: Container runtime

## Deployment Steps

1. **Prepare Kubernetes Manifests**:
Create a `deployment.yaml` file with the following content:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
    name: rick-morty-api
spec:
    replicas: 1
    selector:
    matchLabels:
        app: rick-morty-api
    template:
    metadata:
        labels:
        app: rick-morty-api
    spec:
        containers:
        - name: rick-morty-api
        image: <docker-image-name>
        ports:
        - containerPort: 8000
```

Create a `service.yaml` file with the following content:
```yaml
apiVersion: v1
kind: Service
metadata:
    name: rick-morty-api-service
spec:
    selector:
    app: rick-morty-api
    ports:
    - protocol: TCP
    port: 80
    targetPort: 8000
    type: LoadBalancer
```

2. **Apply the Manifests**:
Apply the deployment and service to your Minikube cluster:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

3. **Verify the Deployment**:
Check the status of your deployment and service:
```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

## Port Forwarding
To access the application, you can use port forwarding:
```bash
kubectl port-forward svc/rick-morty-api-service 8080:80
```
Then, open your browser and navigate to `http://localhost:8080`.

## Cleanup
To delete the deployment and service, run:
```bash
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
```

To stop Minikube and clean up the cluster, run:
```bash
minikube stop
minikube delete
```

To remove the Docker images, run:
```bash
docker rmi <docker-image-name>
```

