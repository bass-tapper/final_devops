## Step 2: Containerization

### Docker Implementation

#### Dockerfile Composition
```dockerfile
FROM python:3.11-slim        # Official lightweight Python image
WORKDIR /app                # Set container working directory
COPY . .                    # Include script + requirements
RUN pip install requests    # Install HTTP client dependency
CMD ["python", "rick-morty-api.py"]  # Execution trigger
```

#### Build Pipeline
```bash
# Build image with name/tag
docker build -t rick-morty-script .

# Run with persistent storage
docker run -v ${PWD}/output:/app/output rick-morty-script
```

### Critical Design Decisions
1. **Volume Mount**: Maps host's `./output` to container's `/app/output` directory to preserve CSV after container termination
2. **Security Optimization**: Slim image variant removes unnecessary packages reducing attack surface
3. **File Isolation**: COPY instruction ensures only relevant project files are included in image
4. **Reproducibility**: Explicit Python version prevents dependency drift

### Verification Steps
```bash
# Validate image construction
docker images | grep rick-morty-script

# Check CSV generation
ls -l output/rick_morty_characters.csv

# Inspect container logs
docker logs <container_id>
```

