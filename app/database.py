"""Database tools"""
# pylint: disable=broad-except

import logging
import os

import psycopg2
from pandas import DataFrame
from sqlalchemy import create_engine

_logger = logging.getLogger(__name__)


class Database:
    """Database"""

    connection = False
    engine = False
    table = ""
    pg_host = "db"
    pg_port = 5432
    pg_db = ""
    pg_user = ""
    pg_password = ""

    def __init__(self):
        """Init"""
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT")
        self.pg_db = os.getenv("PG_DB")
        self.pg_user = os.getenv("PG_USER")
        self.pg_password = os.getenv("PG_PASSWORD")

        self.connection = psycopg2.connect(
            database=self.pg_db,
            user=self.pg_user,
            password=self.pg_password,
            host=self.pg_host,
            port=self.pg_port,
        )

        url = "postgresql://"
        url += f"{self.pg_user}:{self.pg_password}@{self.pg_host}:{int(self.pg_port)}/{self.pg_db}"
        self.engine = create_engine(url)

    def delete_from_df(self, table_name: str, df_data: DataFrame):
        """_summary_

        Args:

        """
        if len(df_data) == 0:
            return

        try:
            with self.engine.connect() as conn:
                df_data.reset_index()
                for index, row in df_data.iterrows():

                    cuit = row["cuit"]
                    date_from = row["fecha_vigencia_desde"].strftime("%Y-%m-%dT%H:%M:%S")
                    date_to = row["fecha_vigencia_hasta"].strftime("%Y-%m-%dT%H:%M:%S")

                    where = f"""
                    cuit = '{cuit}'
                    AND fecha_vigencia_desde = '{date_from}'
                    AND fecha_vigencia_hasta = '{date_to}'
                    """
                    conn.execute(f"DELETE FROM {table_name} WHERE {where}")
                    _logger.info(f"Deleted row: {cuit} | {date_from} | {date_to}")

        except Exception as ex:
            _logger.error(ex)
