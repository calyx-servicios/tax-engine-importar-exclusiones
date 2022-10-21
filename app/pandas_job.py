"""Pandas Job"""
import asyncio
import logging
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy.engine import Engine

_logger = logging.getLogger(__name__)


def format_date(_date):
    """Format date"""
    if isinstance(_date, str):
        _date = datetime.strptime(_date, "%d%m%Y")
    return _date


class PandasJob:
    """Pandas Job"""

    df = False
    chunk_size = 50000

    def read_file(self, file_path):
        """Read file and returns as dataframe

        Args:
            file_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        df_data = pd.read_csv(
            file_path,
            encoding="ISO-8859-1",
            skipinitialspace=True,
            delimiter=",",
            index_col=False,
        )

        return df_data

    async def insert_df_async(self, *args, **kwargs):
        """_summary_

        Returns:
            _type_: _description_
        """
        return await asyncio.to_thread(self.file_to_dataframe, *args, **kwargs)

    def file_to_dataframe(self, df_data: pd.DataFrame, table, engine: Engine):
        """File to dataframe"""
        try:
            _logger.info("=== File to dataframe ===")

            df_data["id"] = None

            df_data["id"] = df_data["id"].map(lambda _: uuid.uuid4())

            df_data.to_sql(table, engine, if_exists="append", index=False, method="multi")

            _logger.info("Dataframe inserted in database.")

        except Exception as ex:
            _logger.error("Dataframe creation error: %s", ex)
            raise ex
