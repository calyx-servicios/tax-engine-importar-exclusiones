"""Database tools"""
# pylint: disable=broad-except

import asyncio
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

    def drop_table(self, table_name: str):
        """Drops table from database

        Args:
            table_name (str): _description_
        """
        with self.engine.connect() as conn:
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    def add_id_to_table(self, table_name: str):
        """_summary_

        Args:
            table_name (str): _description_
        """
        query = f"ALTER TABLE {table_name} ADD PRIMARY KEY ('id');"
        with self.engine.connect() as con:
            con.execute(query)

    async def delete_from_df_async(self, *args):
        """_summary_"""
        return await asyncio.to_thread(self.delete_from_df, *args)

    def delete_from_df(self, table_name: str, df_data: DataFrame):
        """_summary_

        Args:

        """

        if df_data.shape[0] == 0:
            return

        _logger.info("Selecting IDs from database. %d rows remaining.", df_data.shape[0])

        query = f"""
        SELECT id FROM {table_name} WHERE cuit IN {tuple(df_data["cuit"])}
        AND fecha_desde IN {tuple(df_data["fecha_desde"])}
        AND fecha_hasta IN {tuple(df_data["fecha_hasta"])}
        """

        try:
            with self.engine.connect() as conn:
                results = conn.execute(query)
                id_list = map(lambda x: x[0], results.fetchall())
                _logger.info("Deleting rows from database.")
                conn.execute(f"DELETE FROM {table_name} WHERE id IN {tuple(id_list)}")
        except Exception as ex:
            _logger.error(ex)
