#!/usr/bin/env python3
# pylint: disable=invalid-name
# pylint: disable=broad-except
# pylint: disable=duplicate-code,no-name-in-module

import logging
import os
import time

import psycopg2

_logger = logging.getLogger(__name__)

POSTGRES = "postgres"


class Database:
    """Database"""

    connection = False
    engine = False
    session = False
    base = False
    pg_host = "db"
    pg_port = 5432
    pg_db = ""
    pg_user = ""
    pg_password = ""

    def __init__(self):
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT")
        self.pg_db = os.getenv("PG_DB")
        self.pg_user = os.getenv("PG_USER")
        self.pg_password = os.getenv("PG_PASSWORD")

        try:
            _logger.info("Connect to DB %s", self.pg_host)
            self.connection = psycopg2.connect(
                database=POSTGRES,
                user=self.pg_user,
                password=self.pg_password,
                host=self.pg_host,
                port=self.pg_port,
            )
            self.connection.autocommit = True
        except Exception as ex:
            _logger.error("Database connection error: %s", ex)
            raise ex

    def check_db(self):
        """Check DB"""
        connection = False
        try:
            _logger.info("Connect to DB %s", self.pg_host)
            connection = psycopg2.connect(
                database=self.pg_db,
                user=self.pg_user,
                password=self.pg_password,
                host=self.pg_host,
                port=self.pg_port,
            )
        except Exception as ex:
            _logger.error("Database connection error: %s", ex)
        return connection

    def create_db(self):
        """_summary_"""
        with self.connection.cursor() as cursor:
            _logger.debug("Creating Database: %s", self.pg_db)
            cursor.execute(f"CREATE DATABASE {self.pg_db};")


if __name__ == "__main__":
    start_time = time.time()
    database = False
    while (time.time() - start_time) < 30:
        try:
            database = Database()
            if not database.check_db():
                database.create_db()
            database.connection.close()
            error = ""
            break
        except psycopg2.OperationalError as e:
            _logger.exception(e)
            error = e
        time.sleep(1)
