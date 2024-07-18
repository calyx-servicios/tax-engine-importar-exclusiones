"""Bot Tools"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from typing import Tuple

from database import Database
from pandas import DataFrame
from pandas_job import PandasJob
from submodules.box_sm.box import Box

_logger = logging.getLogger(__name__)
logging.getLogger("boxsdk").setLevel(logging.WARNING)


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
        self._box = Box()
        self.input_folder = os.getenv("INPUT_FOLDER_ID")
        self.output_folder = os.getenv("OUTPUT_FOLDER_ID")
        self._main_folder = os.getenv("MAIN_FOLDER_ID")
        self._loop = asyncio.get_event_loop()
        self._output_path = os.getenv("OUTPUT_PATH")
        self._table_name = os.getenv("TABLE_NAME")
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
        df_data["fecha_vigencia_desde"] = df_data["fecha_vigencia_desde"].map(
            lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S") if isinstance(x, str) else x
        )

        df_data["fecha_vigencia_hasta"] = df_data["fecha_vigencia_hasta"].map(
            lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S") if isinstance(x, str) else x
        )

        df_data["cuit"] = df_data["cuit"].astype(str)

        return df_data

    def divide_alta_baja(self, df_data: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Divide dataframe in altas and bajas

        Args:
            df_data (DataFrame): _description_

        Returns:
            Tuple[DataFrame, DataFrame]: _description_
        """

        df_altas = df_data[df_data["alta_baja"] == "A"]
        df_altas = df_altas.drop(["alta_baja"], axis=1)
        df_bajas = df_data[df_data["alta_baja"] == "B"]

        return df_altas, df_bajas

    async def job(self):
        """Job"""
        main_folder_id = self._main_folder
        folder_id_input = self._box.get_folder_id_from_all_files(
            folder_name="Input",
            folder_id=main_folder_id,
        )[0]
        files = self._box.download_files(self._output_path, self.input_folder)

        for f_upload in files:
            _logger.info("Processing file %s", f_upload["name"])

            data = self.format_file(self._pandas_job.read_file(f_upload["name"], self._output_path))

            altas, bajas = self.divide_alta_baja(data)

            self._database.delete_from_df(self._table_name, bajas)

            tasks = []

            tasks.append(
                asyncio.create_task(
                    self._pandas_job.insert_df_async(altas, self._table_name, self._database.engine)
                )
            )

            self._box.upload_files(self.output_folder, f"{self._output_path}/{f_upload['name']}")
            items_to_delete = self._box.get_all_items_of_folder(folder_id_input, "file")
            items_to_delete[0]["file_id"] = items_to_delete[0]["id"]
            self._box.delete_files(items_to_delete)

            await asyncio.gather(*tasks, return_exceptions=False)

        _logger.info("====End Bot===")

        shutil.rmtree(self._output_path, ignore_errors=True)
