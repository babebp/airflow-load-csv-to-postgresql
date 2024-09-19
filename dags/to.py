from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import pandas as pd
import psycopg2

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1
}

# Define the DAG
with DAG('csv_to_postgres_dag', default_args=default_args, schedule_interval='@daily') as dag:

    def load_csv_to_postgres():
        conn = psycopg2.connect(dbname="airflow_db", user="airflow", password="airflow", host="postgres")
        cursor = conn.cursor()

        # Load CSV file
        df = pd.read_csv('/opt/airflow/dags/data.csv')  # CSV file is in the same directory as DAGs

        # Insert data into PostgreSQL
        for index, row in df.iterrows():
            cursor.execute("INSERT INTO my_table (column1, column2) VALUES (%s, %s)", (row['col1'], row['col2']))

        conn.commit()
        cursor.close()
        conn.close()

    def fetch_first_10_rows_from_postgres():
        conn = psycopg2.connect(dbname="airflow_db", user="airflow", password="airflow", host="postgres")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM my_table LIMIT 10")
        rows = cursor.fetchall()
        print(rows)  # Airflow logs will display this
        cursor.close()
        conn.close()

    # Task 1: Load CSV into PostgreSQL
    load_csv_task = PythonOperator(
        task_id='load_csv_to_postgres',
        python_callable=load_csv_to_postgres
    )

    # Task 2: Fetch first 10 rows from PostgreSQL
    fetch_data_task = PythonOperator(
        task_id='fetch_first_10_rows',
        python_callable=fetch_first_10_rows_from_postgres
    )

    # Define task dependencies
    load_csv_task >> fetch_data_task
