# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os
import psycopg2

from loguru import logger


class Database():

    config = {}
    conn = False
    cur = False

    def load_config(self):
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'config', 'config.env'))
        self.config = {
            'POSTGRESQL_HOST': os.getenv('POSTGRESQL_HOST'),
            'POSTGRESQL_PORT': os.getenv('POSTGRESQL_PORT'),
            'POSTGRESQL_DATABASE_NAME': os.getenv('POSTGRESQL_DATABASE_NAME'),
            'POSTGRESQL_USER': os.getenv('POSTGRESQL_USER'),
            'POSTGRESQL_PASSWORD': os.getenv('POSTGRESQL_PASSWORD')
        }
        return self.config

    def get_db_connection(self):
        self.load_config()
        self.conn = psycopg2.connect(
            host=self.config['POSTGRESQL_HOST'],
            port=self.config['POSTGRESQL_PORT'],
            dbname=self.config['POSTGRESQL_DATABASE_NAME'],
            user=self.config['POSTGRESQL_USER'],
            password=self.config['POSTGRESQL_PASSWORD']
        )
        self.cur = self.conn.cursor()

    def end_db_connection(self):
        try:
            self.conn.commit()
            self.cur.close()
            self.conn.close()
        except Exception as e:
            logger.info('End database connection with error\n')
            logger.info(e)
        return True
