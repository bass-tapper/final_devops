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
