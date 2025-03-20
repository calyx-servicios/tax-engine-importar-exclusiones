"""Pandas Job"""

import asyncio
import logging
import os

import pandas as pd
from sqlalchemy.engine import Engine

_logger = logging.getLogger(__name__)


class PandasJob:
    """Pandas Job"""

    df = False
    chunk_size = 50000

    def read_file(self, file_path, output_path):
        """Read file and returns as dataframe

        Args:
            file_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        full_path = f"{output_path}/{file_path}"
        try:
            df_data = pd.read_csv(
                full_path,
                encoding="utf-8-sig",
                skipinitialspace=True,
                delimiter=",",
                decimal=".",
                index_col=False,
                header=None,
                dtype={"alicuota": float},
                parse_dates=[
                    "fecha_vigencia_desde",
                    "fecha_vigencia_hasta",
                ],
                names=[
                    "cuit",
                    "regimen",
                    "fecha_vigencia_desde",
                    "fecha_vigencia_hasta",
                    "alta_baja",
                    "descripcion",
                    "alicuota",
                ],
            )
        except ValueError as ex:
            _logger.error(
                (
                    "El csv subido contiene un formato incorrecto en alguna"
                    "columna. Revisar y volver a ejectuar."
                )
            )
            raise ex

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

            df_data_cleaned.drop(
                [
                    "descripcion_x",
                    "descripcion_y",
                    "regimen",
                    "id",
                    "codigo",
                    "minimo_imponible",
                    "alicuota_default",
                    "alicuota_locales",
                    "alicuota_convenio",
                    "requiere_situacion_iva",
                    "nombre_impuesto_odoo",
                    "jurisdiccion_sircar",
                    "alicuota_2",
                    "alicuota_3",
                ],
                axis=1,
                inplace=True,
            )

            df_data_cleaned.to_sql(table, engine, if_exists="append", index=False, method="multi")

            _logger.info("Dataframe inserted in database.")

        except Exception as ex:
            _logger.error("Dataframe creation error: %s", ex)
            raise ex
