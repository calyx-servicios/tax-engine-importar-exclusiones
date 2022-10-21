"""Bot Tools"""
import asyncio
import logging
import os
import shutil
from datetime import datetime
from typing import Tuple

from database import Database
from odoo import Odoo
from pandas import DataFrame
from pandas_job import PandasJob

_logger = logging.getLogger(__name__)


class Bot:
    """Bot"""

    # Database
    _database = False
    # Pandas
    _pandas_job = False
    # Selenium
    _selenium_job = False
    # Odoo
    _odoo_job = False

    # Dependency

    def __init__(self):
        """Init"""
        _logger.info("====Starting Bot===")
        self._database = Database()
        self._pandas_job = PandasJob()
        self._odoo_job = Odoo()
        self._loop = asyncio.get_event_loop()
        self._output_path = os.getenv("OUTPUT_PATH")
        os.makedirs(self._output_path, exist_ok=True)

    def process(self):
        """Entrypoint"""
        self._loop.run_until_complete(self.job())

    def format_file(self, df_data: DataFrame):
        """_summary_

        Args:
            df_data (DataFrame): _description_

        Returns:
            _type_: _description_
        """
        df_data["fecha_desde"].map(
            lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S") if isinstance(x, str) else x
        )

        df_data["fecha_hasta"].map(
            lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S") if isinstance(x, str) else x
        )

        df_data["cuit_sujeto"] = df_data["cuit_sujeto"].astype(str)

        return df_data

    def divide_alta_baja(self, df_data: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Divide dataframe in altas and bajas

        Args:
            df_data (DataFrame): _description_

        Returns:
            Tuple[DataFrame, DataFrame]: _description_
        """

        df_altas = df_data[df_data["alta_baja"] == "A"]
        df_bajas = df_data[df_data["alta_baja"] == "B"]

        return df_altas, df_bajas

    async def job(self):
        """Job"""
        files = self._odoo_job.get_files(self._output_path)

        for f_upload in files:
            _logger.info("Processing file %s", f_upload["path"])

            data = self.format_file(self._pandas_job.read_file(f_upload["path"]))

            altas, bajas = self.divide_alta_baja(data)

            basename, ext = os.path.splitext(os.path.basename(f_upload["path"]))

            tasks = []

            tasks.append(asyncio.create_task(self._database.delete_from_df_async("test", bajas)))

            tasks.append(
                asyncio.create_task(
                    self._pandas_job.insert_df_async(altas, "test", self._database.engine)
                )
            )

            tasks.append(
                asyncio.create_task(
                    self._odoo_job.upload_file_async(
                        f'{basename}_{datetime.now().strftime("%d_%m_%Y %H_%M")}{ext}',
                        f_upload["path"],
                    )
                )
            )

            tasks.append(asyncio.create_task(self._odoo_job.delete_file_async(f_upload["id"])))

            await asyncio.gather(*tasks, return_exceptions=False)

        _logger.info("====End Bot===")

        shutil.rmtree(self._output_path, ignore_errors=True)
