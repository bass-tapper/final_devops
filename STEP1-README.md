## API Script: rick-morty-api.py

### Functionality
- Fetches paginated data from Rick & Morty API
- Filters: Species=Human, Status=Alive, Origin=Earth (C-137 dimension)
- Stores: Character name, location name, image URL

### Execution Flow
```python
Loop until no next page:
    1. GET {{current_url}}
    2. Process JSON → extract fields
    3. Append results → characters list
    4. Update url ← next page URL
Write CSV: Name | Location | Image_URL
```

### Execution Requirements
- Requests library (`pip install requests`)
- Python ≥3.7 (macOS default ≥3.9)

