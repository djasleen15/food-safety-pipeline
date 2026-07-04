import snowflake.connector
import os
import json
import pandas as pd
from datetime import datetime
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

load_dotenv()


def get_snowflake_connection():
    """Create and return an authenticated Snowflake connection."""
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        schema='raw'
    )


def get_adls_client():
    """Create and return an authenticated ADLS2 client."""
    return DataLakeServiceClient(
        account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.dfs.core.windows.net",
        credential=os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    )


def read_from_adls(container, path):
    """Read a file from ADLS2 and return its contents as bytes."""
    client = get_adls_client()
    file_system_client = client.get_file_system_client(container)
    file_client = file_system_client.get_file_client(path)
    download = file_client.download_file()
    return download.readall()


def load_fda_recalls(conn, date_str):
    """
    Read FDA recalls JSON from ADLS2 and load into
    Snowflake raw.fda_recalls table.
    """
    path = f"fda/recalls/{date_str}/recalls.json"
    print(f"Reading FDA data from {path}...")

    raw_bytes = read_from_adls("raw", path)
    records = json.loads(raw_bytes)

    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        create table if not exists raw.fda_recalls (
            status varchar,
            city varchar,
            state varchar,
            country varchar,
            classification varchar,
            product_type varchar,
            event_id varchar,
            recalling_firm varchar,
            address_1 varchar,
            postal_code varchar,
            voluntary_mandated varchar,
            initial_firm_notification varchar,
            distribution_pattern varchar,
            recall_number varchar,
            product_description varchar,
            product_quantity varchar,
            reason_for_recall varchar,
            recall_initiation_date varchar,
            center_classification_date varchar,
            termination_date varchar,
            report_date varchar,
            code_info varchar,
            ingested_at timestamp default current_timestamp
        )
    """)

    # Insert records
    cursor.execute("truncate table raw.fda_recalls")

    insert_sql = """
        insert into raw.fda_recalls (
            status, city, state, country, classification,
            product_type, event_id, recalling_firm, address_1,
            postal_code, voluntary_mandated, initial_firm_notification,
            distribution_pattern, recall_number, product_description,
            product_quantity, reason_for_recall, recall_initiation_date,
            center_classification_date, termination_date, report_date,
            code_info
        ) values (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s
        )
    """

    rows = [
        (
            r.get('status'), r.get('city'), r.get('state'),
            r.get('country'), r.get('classification'),
            r.get('product_type'), r.get('event_id'),
            r.get('recalling_firm'), r.get('address_1'),
            r.get('postal_code'), r.get('voluntary_mandated'),
            r.get('initial_firm_notification'),
            r.get('distribution_pattern'), r.get('recall_number'),
            r.get('product_description'), r.get('product_quantity'),
            r.get('reason_for_recall'), r.get('recall_initiation_date'),
            r.get('center_classification_date'), r.get('termination_date'),
            r.get('report_date'), r.get('code_info')
        )
        for r in records
    ]

    cursor.executemany(insert_sql, rows)
    conn.commit()
    print(f"Loaded {len(rows)} FDA recall records into raw.fda_recalls")
    cursor.close()


def load_cdc_outbreaks(conn, date_str):
    """
    Read CDC outbreaks CSV from ADLS2 and load into
    Snowflake raw.cdc_outbreaks table.
    """
    path = f"cdc/outbreaks/{date_str}/outbreaks.csv"
    print(f"Reading CDC data from {path}...")

    raw_bytes = read_from_adls("raw", path)
    df = pd.read_csv(pd.io.common.BytesIO(raw_bytes))
    df = df.where(pd.notnull(df), None)

    cursor = conn.cursor()

    cursor.execute("""
        create table if not exists raw.cdc_outbreaks (
            year varchar,
            month varchar,
            state varchar,
            primary_mode varchar,
            etiology varchar,
            serotype_or_genotype varchar,
            etiology_status varchar,
            setting varchar,
            illnesses varchar,
            hospitalizations varchar,
            deaths varchar,
            food_vehicle varchar,
            food_contaminated_ingredient varchar,
            ifsac_category varchar,
            water_exposure varchar,
            water_type varchar,
            animal_type varchar,
            ingested_at timestamp default current_timestamp
        )
    """)
    cursor.execute("truncate table raw.cdc_outbreaks")

    insert_sql = """
        insert into raw.cdc_outbreaks (
            year, month, state, primary_mode, etiology,
            serotype_or_genotype, etiology_status, setting,
            illnesses, hospitalizations, deaths,
            food_vehicle, food_contaminated_ingredient,
            ifsac_category, water_exposure, water_type, animal_type
        ) values (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s
        )
    """

    def clean(val):
        """Convert NaN to None, otherwise return string."""
        if val is None:
            return None
        if pd.isna(val):
            return None
        return str(val)

    rows = [
        (
            clean(r.get('Year')), clean(r.get('Month')),
            clean(r.get('State')), clean(r.get('Primary Mode')),
            clean(r.get('Etiology')), clean(r.get('Serotype or Genotype')),
            clean(r.get('Etiology Status')), clean(r.get('Setting')),
            clean(r.get('Illnesses')), clean(r.get('Hospitalizations')),
            clean(r.get('Deaths')), clean(r.get('Food Vehicle')),
            clean(r.get('Food Contaminated Ingredient')),
            clean(r.get('IFSAC Category')), clean(r.get('Water Exposure')),
            clean(r.get('Water Type')), clean(r.get('Animal Type'))
        )
        for _, r in df.iterrows()
    ]

    cursor.executemany(insert_sql, rows)
    conn.commit()
    print(f"Loaded {len(rows)} CDC outbreak records into raw.cdc_outbreaks")
    cursor.close()


def run():
    """Main entry point for Snowflake loader."""
    print("Starting Snowflake loader...")
    date_str = datetime.now().strftime("%Y/%m/%d")

    conn = get_snowflake_connection()

    try:
        load_fda_recalls(conn, date_str)
        load_cdc_outbreaks(conn, date_str)
    finally:
        conn.close()

    print("Snowflake loading complete.")


if __name__ == "__main__":
    run()