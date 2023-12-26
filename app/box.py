import requests
import os
import uuid
from shutil import copyfile
from typing import List
from boxsdk import OAuth2, Client


class Box:
    """_summary_"""

    def __init__(
        self,
        logger: object,
    ) -> None:  # ,logger: object
        self.client, self.time_exp = self.get_auth(
            os.getenv("BOX_GRANT_TYPE"),
            os.getenv("BOX_CLIENT_ID"),
            os.getenv("BOX_CLIENT_SECRET"),
            os.getenv("BOX_SUBJECT_ID"),
            os.getenv("BOX_SUBJECT_TYPE"),
            logger,
        )
        self.logger = logger
        folder_id_main = self.get_folder_id_from_all_files(
            folder_name="Supermercados Dia", folder_id=0
        )[0]
        if os.getenv("BOX_ENV") == "PROD":
            folder_id_clientes = self.get_folder_id_from_all_files(
                folder_name="Clientes", folder_id=folder_id_main
            )[0]
        else:
            folder_id_clientes = self.get_folder_id_from_all_files(
                folder_name="Clientes", folder_id=folder_id_main
            )[0]

        self._folder_box = folder_id_clientes

    def get_files(self, output_path: str) -> List[str]:
        """_summary_

        Args:
            output_path (str): _description_

        Returns:
            List[str]: _description_
        """
        files = []
        list_facturas = self.get_all_items_of_folder(self._folder_box, "file")
        for factura in list_facturas:
            if "tax-engine" not in factura["name"]:
                self.download_file(factura, output_path)
                new_path = f"{output_path}/{factura['name']}"
                files.append({"path": new_path, "id": str(uuid.uuid4())})
        return files

    def upload_file(self, name, filename):
        """_summary_

        Args:
            name (_type_): _description_
            filename (_type_): _description_
        """
        copyfile(filename, name)
        self.upload_files(self._folder_box, name)
        self.logger.info(f"Se cargo en box con exito el archivo {name}")

    def delete_file(self, fileid):
        """_summary_

        Args:
            fileid (_type_): _description_
        """
        path_file = os.path.dirname(fileid)
        if os.path.exists(path_file):
            os.remove(fileid)
        list_files = self.get_all_items_of_folder(self._folder_box, "file")
        self.remove_files_folder(list_files)

    def get_all_items_of_folder(self, folder_id: int, item_type: str) -> list:
        """Retorna una lista con todos los archivos de un tipo en especifico del id de carpeta
        pasado por parametro

        Args:
            folder_id (int): _description_
            item_type (str): _description_

        Returns:
            list: _description_
        """
        all_files = []
        items = self.client.folder(
            folder_id=folder_id
        ).get_items()  # el folder 0 es la carpeta principal
        for item in items:
            type_item = item.type
            if type_item == item_type:
                all_files.append({"type": item.type, "id": item.id, "name": item.name})
        return all_files

    def get_folder_id_from_all_files(self, folder_name: str, folder_id: int = 0) -> str:
        """Retorna el id de la carpeta segun el nombre de la misma

        Args:
            folder_name (str): _description_
            folder_id (int, optional): _description_. Defaults to 0.

        Returns:
            str: _description_
        """
        all_folders = self.get_all_items_of_folder(folder_id=folder_id, item_type="folder")
        for item in all_folders:
            if item["name"] == folder_name:
                folder_id = item["id"]
                folder_name = item["name"]
                break

        if folder_id == 0:
            # Validacion para identificar carpeta inicio de box
            return "0"

        return folder_id, folder_name

    def upload_files(
        self,
        folder_id: int,
        file_path: str,
    ) -> None:
        """API BOX post upload files to specific folder with folder id.

        Args:
            folder_id (int): _description_
            file_path (str): _description_
            flag_metadata (bool, optional): _description_. Defaults to False.
            df_invoice (_type_, optional): _description_. Defaults to None.
        """
        try:
            all_files = self.get_all_items_of_folder(folder_id, item_type="file")
            flag_exits = False
            if len(file_path.split("/")) == 5:
                file_name = file_path.split("/")[4]
                for file in all_files:
                    if file["name"] == file_name:
                        flag_exits = True
                        break
            if not flag_exits:
                file = self.client.folder(folder_id=folder_id).upload(file_path)
            else:
                self.logger.info(f"Ya existe este archivo {file_name}")
        except Exception as error:
            message = f"Hubo un error con la subida del archivo: - Exception: {error}"
            self.logger.error(message)

    def download_file(self, factura, download_path):
        try:
            output_file = open(f"{download_path}/{factura['name']}", "wb")
            self.client.file(file_id=factura["id"]).download_to(output_file)
            self.logger.info(f"Se descargo con exito el archivo {factura['name']}")
        except Exception as error:
            message = (
                f"No se pudo descargar el archivo {factura['name']}.\n"
                f"Por el siguente error {error}"
            )
            self.logger.error(message)

    def remove_files_folder(self, list_files_del):
        """Elimina archivos en carpetas mediante el ID
            de los mismos

        Args:
            list_files_del (list): lista de archivos con name, id y otros
        """
        try:
            for file_del in list_files_del:
                if "tax-engine" not in file_del["name"]:
                    self.client.file(file_id=file_del["id"]).delete()
        except Exception as error:
            self.logger.error(f"Problemas para eliminar {file_del['name']}")
            self.logger.error(f"Detalle error: {error}")

    def get_auth(self, grant_type, client_id, secret_client, subject_id, subject_type, logger):
        try:
            """_summary_
            Args:
                grant_type (_type_): _description_
                client_id (_type_): _description_
                secret_client (_type_): _description_
                subject_id (_type_): _description_
                subject_type (_type_): _description_
                metadata_template (_type_): _description_
                logger (_type_): _description_
            Returns:
                _type_: _description_
            """
            access_token, expires_in = self.get_access_token(
                grant_type, client_id, secret_client, subject_type, subject_id
            )
            box_client = self.get_client(client_id, secret_client, access_token)
            return box_client, expires_in
        except Exception as error:
            raise error

    def get_access_token(
        self, grant_type, client_id, client_secret, box_subject_type, box_subject_id
    ) -> str:
        """_summary_
        Args:
            grant_type (_type_): _description_
            client_id (_type_): _description_
            client_secret (_type_): _description_
            box_subject_type (_type_): _description_
            box_subject_id (_type_): _description_
        Returns:
            str: _description_
        """
        post_auth_url = "https://api.box.com/oauth2/token/"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": grant_type,
            "box_subject_type": box_subject_type,
            "box_subject_id": box_subject_id,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth_responce = requests.post(post_auth_url, data=payload, headers=headers, timeout=2000)
        if auth_responce.status_code == 200:
            auth_responce = auth_responce.json()
            if "access_token" in auth_responce:
                token = auth_responce["access_token"]
                expires_in = auth_responce["expires_in"]
                return token, expires_in
        return "0", "0"

    def get_client(self, client_id, client_secret, token):
        """_summary_
        Args:
            client_id (_type_): _description_
            client_secret (_type_): _description_
            token (_type_): _description_
        Returns:
            _type_: _description_
        """
        if token != "0":
            oauth = OAuth2(client_id=client_id, client_secret=client_secret, access_token=token)

            client = Client(oauth)

            return client
        return "no_client_box"

    def refresh_token_func(client_id, client_secret, token, refresh_token):
        auth = OAuth2(
            client_id=client_id,
            client_secret=client_secret,
            access_token=token,
            refresh_token=refresh_token,
        )

        client = Client(auth)

        user = client.user().get()
        print(f"User ID is {user.id}")
