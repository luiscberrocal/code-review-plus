import requests

def get_image_versions(image_name:str):
    """
    Fetches and prints all available tags for the official Python image on Docker Hub.
    """
    base_url = f"https://hub.docker.com/v2/repositories/library/{image_name}/tags"
    all_versions = []
    page = 1
    page_size = 100  # You can increase this to reduce the number of requests

    while True:
        params = {
            'page': page,
            'page_size': page_size
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            # Extract tag names from the results and add to our list
            for result in data['results']:
                all_versions.append(result['name'])

            # Check for the next page
            if data['next']:
                page += 1
            else:
                break  # No more pages to retrieve
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break

    return sorted(all_versions)

if __name__ == "__main__":
    print("Fetching all Python image versions from Docker Hub...")
    versions = get_image_versions(image_name="postgres")

    if versions:
        print(f"Found {len(versions)} tags for the official Python image:")
        for version in versions:
            print(version)
    else:
        print("Could not retrieve any versions.")