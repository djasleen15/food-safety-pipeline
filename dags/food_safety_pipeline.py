from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="food_safety_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",
    catchup=False,
    tags=["food-safety"],
    description="Weekly ELT pipeline ingesting FDA recall and CDC outbreak data"
) as dag:

    ingest_fda = BashOperator(
        task_id="ingest_fda_recalls",
        bash_command="cd /opt/airflow && python ingestion/fda_recalls.py"
    )

    ingest_cdc = BashOperator(
        task_id="ingest_cdc_outbreaks",
        bash_command="cd /opt/airflow && python ingestion/cdc_outbreaks.py"
    )

    load_snowflake = BashOperator(
        task_id="load_to_snowflake",
        bash_command="cd /opt/airflow && python loaders/snowflake_loader.py"
    )

    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command="echo 'dbt coming in week 2'"
    )

    [ingest_fda, ingest_cdc] >> load_snowflake >> run_dbt