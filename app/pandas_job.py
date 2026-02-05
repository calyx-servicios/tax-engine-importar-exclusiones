"""Pandas Job"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Iterable

import pandas as pd
from sqlalchemy.engine import Engine

_logger = logging.getLogger(__name__)


def date_parser_func(dates: Iterable):
    """Se encarga de formatear las fechas enviadas en el archivo CSV"""
    try:
        formated_dates = [datetime.strptime(date, "%d/%m/%Y %H:%M:%S") for date in dates]
        return formated_dates
    except ValueError as ex:
        _logger.error(
            "Error en el formato de subida del campo fecha_vigencia_desde o fecha_vigencia_hasta"
        )
        raise ex


class PandasJob:
    """Pandas Job"""

    df = False
    chunk_size = 50000

    def _detect_encoding_and_delimiter(self, file_path: str) -> tuple:
        """Detecta automáticamente la codificación, delimitador y columnas del archivo

        Args:
            file_path (str): Ruta completa del archivo

        Returns:
            tuple: (encoding, delimiter, column_count)
        """
        try:
            # Primero intentamos leer con utf-8-sig (elimina BOM si existe)
            with open(file_path, "r", encoding="utf-8-sig") as f:
                first_line = f.readline().strip()

            encoding = "utf-8-sig"
            _logger.info("Detected encoding: UTF-8 with BOM")
        except UnicodeDecodeError:
            # Si falla, usamos ISO-8859-1
            try:
                with open(file_path, "r", encoding="ISO-8859-1") as f:
                    first_line = f.readline().strip()
                encoding = "ISO-8859-1"
                _logger.info("Detected encoding: ISO-8859-1")
            except Exception as ex:
                _logger.warning(f"Error detecting encoding: {ex}, defaulting to utf-8-sig")
                encoding = "utf-8-sig"
                first_line = ""

        try:
            comma_count = first_line.count(",")
            semicolon_count = first_line.count(";")

            _logger.info(
                f"Detected delimiters - Commas: {comma_count}, Semicolons: {semicolon_count}"
            )

            # Retorna el delimitador que más apariciones tiene
            if semicolon_count > comma_count:
                _logger.info("Using semicolon (;) as delimiter")
                delimiter = ";"
            else:
                _logger.info("Using comma (,) as delimiter")
                delimiter = ","

            column_count = (first_line.count(delimiter) + 1) if first_line else 0
            return encoding, delimiter, column_count
        except Exception as ex:
            _logger.warning(f"Error detecting delimiter: {ex}, defaulting to comma")
            return encoding, ",", 0

    def read_file(self, file_path, output_path):
        """Read file and returns as dataframe

        Args:
            file_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        full_path = f"{output_path}/{file_path}"
        try:
            # Detecta encoding, delimitador y cantidad de columnas automáticamente
            encoding, delimiter, column_count = self._detect_encoding_and_delimiter(full_path)

            all_names = [
                "cuit",
                "regimen",
                "fecha_vigencia_desde",
                "fecha_vigencia_hasta",
                "alta_baja",
                "descripcion",
                "alicuota",
            ]

            if column_count and column_count > len(all_names):
                raise ValueError("El csv tiene más columnas de las esperadas.")

            if column_count <= 0:
                column_count = len(all_names)

            names = all_names[:column_count]
            dtype = {"alicuota": float} if "alicuota" in names else None

            df_data = pd.read_csv(
                full_path,
                encoding=encoding,
                skipinitialspace=True,
                delimiter=delimiter,
                decimal=".",
                index_col=False,
                header=None,
                dtype=dtype,
                parse_dates=[
                    "fecha_vigencia_desde",
                    "fecha_vigencia_hasta",
                ],
                infer_datetime_format=False,
                date_parser=date_parser_func,
                names=names,
            )
        except ValueError as ex:
            _logger.error(
                (
                    "El csv subido contiene un formato incorrecto en alguna"
                    "columna. Revisar y volver a ejectuar."
                )
            )
            raise ex

        if "descripcion" not in df_data.columns:
            df_data["descripcion"] = ""
        if "alicuota" not in df_data.columns:
            df_data["alicuota"] = pd.NA

        df_data = df_data.drop_duplicates()

        df_data["descripcion"] = df_data["descripcion"].astype(str).str.slice(0, 100)

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
            df_data_cleaned = df_data

            try:
                df_data_current = pd.read_sql_table(table, engine)

                # se limpian las filas con que están duplicadas con filas
                # que ya están en la base de datos
                for index, row in df_data_current.iterrows():
                    _logger.info(f"Cleanning row {index}")
                    df_data_cleaned = df_data_cleaned[
                        (df_data_cleaned["cuit"] != row["cuit"])
                        | (df_data_cleaned["fecha_vigencia_desde"] != row["fecha_vigencia_desde"])
                        | (df_data_cleaned["fecha_vigencia_hasta"] != row["fecha_vigencia_hasta"])
                    ]
            except ValueError as ex:
                if str(ex)[:5] == "Table" and str(ex)[-9:] == "not found":
                    _logger.info(f"No existe la tabla {table}")
                else:
                    raise ex

            df_data_cleaned["cuit"] = [str(cuit).strip() for cuit in df_data_cleaned["cuit"]]
            df_data_cleaned["alicuota"] = [
                float(alicuota) for alicuota in df_data_cleaned["alicuota"]
            ]
            df_data_cleaned["regimen"] = [
                str(regimen).strip() for regimen in df_data_cleaned["regimen"]
            ]
            df_data_cleaned["fecha_vigencia_desde"] = [
                str(fecha_vigencia_desde).strip()
                for fecha_vigencia_desde in df_data_cleaned["fecha_vigencia_desde"]
            ]
            df_data_cleaned["fecha_vigencia_hasta"] = [
                str(fecha_vigencia_hasta).strip()
                for fecha_vigencia_hasta in df_data_cleaned["fecha_vigencia_hasta"]
            ]

            df_data_cleaned["descripcion"] = (
                df_data_cleaned["descripcion"].astype(str).str.slice(0, 100)
            )

            df_data_agents = pd.read_sql_table("agentes", engine)
            df_data_regimes = pd.read_sql_table("regimenes", engine)

            agent_id = df_data_agents[df_data_agents["codigo"] == int(os.getenv("AGENTE"))].iat[
                0, 0
            ]
            df_data_cleaned["agente_id"] = agent_id

            df_data_cleaned["regimen"] = df_data_cleaned["regimen"].astype(int)

            df_data_cleaned = df_data_cleaned.merge(
                df_data_regimes, left_on="regimen", right_on="codigo"
            )
            df_data_cleaned["descripcion"] = df_data_cleaned["descripcion_x"].replace({"nan": ""})
            df_data_cleaned["regimen_id"] = list(df_data_cleaned["id"])

            df_data_cleaned = df_data_cleaned[
                [
                    "cuit",
                    "fecha_vigencia_desde",
                    "fecha_vigencia_hasta",
                    "regimen_id",
                    "agente_id",
                    "descripcion",
                    "alicuota",
                ]
            ]

            df_data_cleaned.to_sql(table, engine, if_exists="append", index=False, method="multi")

            _logger.info("Dataframe inserted in database.")

        except Exception as ex:
            _logger.error("Dataframe creation error: %s", ex)
            raise ex
