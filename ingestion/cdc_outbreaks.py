import pandas as pd
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


def load_cdc_data(filepath):
    """
    Read the NORS CSV file and filter to food-related outbreaks only.
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(filepath)
    print(f"Total records loaded: {len(df)}")

    # Filter to food-related outbreaks only
    df = df[df['Primary Mode'] == 'Food']
    print(f"Food-related outbreaks: {len(df)}")

    return df


def upload_to_adls(df, container, path):
    """
    Upload a DataFrame as CSV to ADLS2 at the given path.
    """
    client = get_adls_client()
    file_system_client = client.get_file_system_client(container)
    file_client = file_system_client.get_file_client(path)

    data_bytes = df.to_csv(index=False).encode("utf-8")
    file_client.upload_data(data_bytes, overwrite=True)
    print(f"Uploaded {len(df)} records to {container}/{path}")


def run():
    """Main entry point for CDC outbreak ingestion."""
    print("Starting CDC outbreak ingestion...")

    filepath = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "NORS_20260703.csv"
    )

    df = load_cdc_data(filepath)

    date_str = datetime.now().strftime("%Y/%m/%d")
    path = f"cdc/outbreaks/{date_str}/outbreaks.csv"

    upload_to_adls(df, "raw", path)
    print("CDC ingestion complete.")


if __name__ == "__main__":
    run()