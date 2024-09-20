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

    # Task 1: Create the table if it doesn't exist
    create_table_task = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='airflow_postgresql',  # Use the PostgreSQL connection
        sql="""
        CREATE TABLE IF NOT EXISTS my_table (
            idx SERIAL PRIMARY KEY,
            label TEXT,
            problem TEXT,
            solution TEXT
        );
        """
    )

    # Task 2: Load CSV data into PostgreSQL
    def load_csv_to_postgres():
        conn = psycopg2.connect(dbname="airflow_db", user="airflow", password="airflow", host="postgres")
        cursor = conn.cursor()

        # Load CSV file
        df = pd.read_csv('/opt/airflow/dags/data.csv')  # CSV file is in the same directory as DAGs

        # Insert data into PostgreSQL
        for index, row in df.iterrows():
            cursor.execute("INSERT INTO my_table (label, problem, solution) VALUES (%s, %s, %s)", (row['label'], row['problem'], row['solution']))

        conn.commit()
        cursor.close()
        conn.close()

    load_csv_task = PythonOperator(
        task_id='load_csv_to_postgres',
        python_callable=load_csv_to_postgres
    )

    # Task 3: Fetch first 10 rows and save them as a CSV
    def fetch_first_10_rows_and_save_to_csv():
        conn = psycopg2.connect(dbname="airflow_db", user="airflow", password="airflow", host="postgres")
        cursor = conn.cursor()

        # Fetch the first 10 rows
        cursor.execute("SELECT * FROM my_table LIMIT 10")
        rows = cursor.fetchall()

        # Fetch column names
        column_names = [desc[0] for desc in cursor.description]

        # Create a DataFrame and save it to a CSV
        df = pd.DataFrame(rows, columns=column_names)
        df.to_csv('/opt/airflow/dags/output_first_10_rows.csv', index=False)  # Save CSV to local directory

        cursor.close()
        conn.close()

    fetch_data_task = PythonOperator(
        task_id='fetch_first_10_rows',
        python_callable=fetch_first_10_rows_and_save_to_csv
    )

    # Define task dependencies
    create_table_task >> load_csv_task >> fetch_data_task
