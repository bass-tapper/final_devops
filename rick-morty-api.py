import requests
import csv
import os

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

def fetch_characters():
    """
    Fetches characters from Rick & Morty API that match the criteria:
    - Species: Human
    - Status: Alive
    - Origin: Earth (C-137)
    """
    url = "https://rickandmortyapi.com/api/character"
    characters = []
    
    while url:
        print(f"Fetching data from: {url}")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            break
            
        data = response.json()
        
        # Process results
        for character in data.get('results', []):
            # Apply filters: Human, Alive, from Earth C-137
            if (character.get('species') == 'Human' and 
                character.get('status') == 'Alive' and 
                character.get('origin', {}).get('name') == 'Earth (C-137)'):
                
                # Extract required fields
                characters.append({
                    'name': character.get('name'),
                    'location': character.get('location', {}).get('name'),
                    'image_url': character.get('image')
                })
        
        # Get URL for next page, if any
        url = data.get('info', {}).get('next')
    
    return characters

def save_to_csv(characters):
    """Save filtered characters to CSV file"""
    output_file = 'output/rick_morty_characters.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['name', 'location', 'image_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for character in characters:
            writer.writerow(character)
    
    print(f"Data saved to {output_file}")
    print(f"Total characters found: {len(characters)}")

def main():
    print("Starting Rick & Morty character extraction...")
    characters = fetch_characters()
    
    if characters:
        save_to_csv(characters)
    else:
        print("No matching characters found.")

if __name__ == "__main__":
    main()
