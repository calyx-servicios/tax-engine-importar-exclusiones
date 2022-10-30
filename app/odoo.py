"""ODOO MODULE"""

import asyncio
import base64
import json
import logging
import os
import random
import shutil
import urllib.request
from typing import List

_logger = logging.getLogger(__name__)

# pylint: disable=broad-except


def json_rpc(url, method, params):
    """_summary_

    Args:
        url (_type_): _description_
        method (_type_): _description_
        params (_type_): _description_

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }

    result = None

    req = urllib.request.Request(
        url=url,
        data=json.dumps(data).encode(),
        headers={
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as content:
        reply = json.loads(content.read().decode("UTF-8"))

    if reply.get("error"):
        raise Exception(reply["error"])

    result = reply["result"]

    return result


def call(url, service, method, *args):
    """_summary_

    Args:
        url (_type_): _description_
        service (_type_): _description_
        method (_type_): _description_

    Returns:
        _type_: _description_
    """
    return json_rpc(url, "call", {"service": service, "method": method, "args": args})


class Odoo:
    """Odoo JSON Connector"""

    user = "odoo"
    password = "odoo"
    dbname = "test"
    url = ""
    directory_id = 0

    def __init__(self):
        """Init"""
        _logger.info("Init Odoo Conector")
        self.user = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")
        self.dbname = os.getenv("ODOO_DB")
        self.url = os.getenv("ODOO_URL")

        self.dir_to_process_id = int(os.getenv("ODOO_DIRECTORY_TO_PROCESS", "0"))
        self.dir_processed_id = int(os.getenv("ODOO_DIRECTORY_PROCESSED", "0"))
        _logger.info("Odoo Conector URL: %s", self.url)

    def get_files(self, output_path: str) -> List[str]:
        """Function to fetch all files in "Para procesar" folder

        Returns:
            List[str]: Absolute paths of fetched files
        """
        uid = call(self.url, "common", "login", self.dbname, self.user, self.password)

        file_ids = call(
            self.url,
            "object",
            "execute",
            self.dbname,
            uid,
            self.password,
            "dms.file",
            "search_read",
            [("directory_id", "=", self.dir_to_process_id)],
        )

        files = []

        p_id = self.dir_to_process_id
        _len = len(file_ids)
        _logger.info("Files in Directory %s: %s", p_id, _len)

        for file_id in file_ids:
            _logger.info("File:%s Size:%s", file_id["name"], file_id["size"])
            with open(file_id["name"], "wb") as store:
                store.write(base64.b64decode(file_id["content"]))
                filepath = os.path.realpath(store.name)

            new_path = os.path.join(output_path, os.path.basename(filepath))
            shutil.move(filepath, new_path)
            files.append({"path": new_path, "id": file_id["id"]})

        return files

    async def delete_file_async(self, *args):
        """_summary_

        Returns:
            _type_: _description_
        """
        return await asyncio.to_thread(self.delete_file, *args)

    def delete_file(self, fileid):
        """_summary_

        Args:
            fileid (_type_): _description_
        """
        uid = call(self.url, "common", "login", self.dbname, self.user, self.password)

        try:
            _logger.info("Deleting file %s from ODOO", fileid)
            call(
                self.url,
                "object",
                "execute",
                self.dbname,
                uid,
                self.password,
                "dms.file",
                "unlink",
                fileid,
            )
            _logger.info("File %s deleted from ODOO", fileid)
        except Exception as ex:
            _logger.error(ex)

    async def upload_file_async(self, *args):
        """_summary_

        Returns:
            _type_: _description_
        """
        return await asyncio.to_thread(self.upload_file, *args)

    def upload_file(self, name, filename):
        """_summary_

        Args:
            name (_type_): _description_
            filename (_type_): _description_
        """
        # Cambiar para que tome el id como parametro
        uid = call(self.url, "common", "login", self.dbname, self.user, self.password)

        args = {
            "directory_id": self.dir_processed_id,
            "content": False,
            "name": name,
            "create_uid": uid,
        }

        _logger.info("Uploading %s to ODOO", filename)

        with open(filename, mode="rb") as file:
            _file = file.read()
            args["content"] = base64.encodebytes(_file).decode("utf-8")

            fid = call(
                self.url,
                "object",
                "execute",
                self.dbname,
                uid,
                self.password,
                "dms.file",
                "create",
                args,
            )

            _logger.info("File %s uploaded to ODOO with id %d", filename, fid)
