This is a data engineering portfolio project called food-safety-pipeline.

Stack: Python, Apache Airflow, dbt, Snowflake, Azure Data Lake Storage Gen2, Great Expectations, Metabase.

Project goal: Build a weekly ELT pipeline that ingests FDA food recall data and CDC foodborne illness outbreak data, lands it in Azure Data Lake Storage Gen2, loads it into Snowflake, and transforms it through bronze/silver/gold layers using dbt. The core analytical question is: how long is the lag between a CDC-reported foodborne illness outbreak and the corresponding FDA food recall, broken down by pathogen and food category?

Current stage: Week 1 - environment setup and ingestion layer.

Conventions:
- Python files use snake_case
- All credentials come from .env via python-dotenv, never hardcoded
- Raw data is never transformed at ingestion, only landed as-is
- dbt models are pure SQL
- Every dbt model has not_null and unique tests on its primary key
- Airflow DAGs use the context manager style
- All functions have docstrings
- Commits follow conventional commits: feat:, fix:, docs:, chore:
