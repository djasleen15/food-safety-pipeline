import requests
import json
import os
from datetime import datetime
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

load_dotenv()


def get_adls_client():
    """Create and return an authenticated ADLS2 client."""
    return DataLakeServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.dfs.core.windows.net",
        credential=os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    )


def fetch_fda_recalls():
    """
    Paginate through the FDA enforcement API and return
    all food recall records as a list of dicts.
    """
    base_url = "https://api.fda.gov/food/enforcement.json"
    all_results = []
    limit = 100
    skip = 0

    while True:
        response = requests.get(
            base_url,
            params={"limit": limit, "skip": skip}
        )

        if response.status_code != 200:
            print(f"API error at skip {skip}: {response.status_code}")
            break

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("No more results, stopping pagination.")
            break

        all_results.extend(results)
        print(f"Fetched {len(all_results)} / {data['meta']['results']['total']} records")

        skip += limit

        # FDA API caps accessible records at 26000 via skip parameter
        if skip >= 26000:
            print("Reached FDA API skip limit of 26000.")
            break

    return all_results


def upload_to_adls(data, container, path):
    """
    Upload a list of dicts as JSON to ADLS2 at the given path.
    """
    client = get_adls_client()
    file_system_client = client.get_file_system_client(container)
    file_client = file_system_client.get_file_client(path)

    data_bytes = json.dumps(data, indent=2).encode("utf-8")
    file_client.upload_data(data_bytes, overwrite=True)
    print(f"Uploaded {len(data)} records to {container}/{path}")


def run():
    """Main entry point for FDA recall ingestion."""
    print("Starting FDA recall ingestion...")
    recalls = fetch_fda_recalls()

    date_str = datetime.now().strftime("%Y/%m/%d")
    path = f"fda/recalls/{date_str}/recalls.json"

    upload_to_adls(recalls, "raw", path)
    print("FDA ingestion complete.")


if __name__ == "__main__":
    run()