import os
import sys
import click
import traceback
import logging as log
import psycopg2
import csv

from dotenv import load_dotenv
from pathlib import Path



# log uncaught exceptions
def log_exceptions(type, value, tb):
    for line in traceback.TracebackException(type, value, tb).format(chain=True):
        log.exception(line)

    log.exception(value)

    sys.__excepthook__(type, value, tb) # calls default excepthook


def connect_database(env_path):
    try:
        load_dotenv(dotenv_path=Path(env_path))

        conn = psycopg2.connect(
            database = os.getenv('DB_NAME'),
            password = os.getenv('DB_PASS'),
            user = os.getenv('DB_USER'),
            host = os.getenv('DB_HOST'),
            port = os.getenv('DB_PORT')
        )

        conn.autocommit = True

        log.info('connection to database established')

        return conn
    except Exception as e:
        log.error(e)

        sys.exit(1)


def insert_row_hh(cur, row):
    code = row['code']
    designation = row['designation']

    sql = '''
        INSERT INTO hh_biotope_key (code, designation) VALUES (%s, %s) RETURNING id
    '''

    try:
        cur.execute(sql, (code, designation))

        last_inserted_id = cur.fetchone()[0]

        log.info(f'inserted {code} with id {last_inserted_id}')
    except Exception as e:
        log.error(e)


def insert_row_sh(cur, row):
    code = row['code']
    designation = row['designation']

    sql = '''
        INSERT INTO sh_biotope_key (code, designation) VALUES (%s, %s) RETURNING id
    '''

    try:
        cur.execute(sql, (code, designation))

        last_inserted_id = cur.fetchone()[0]

        log.info(f'inserted {code} with id {last_inserted_id}')
    except Exception as e:
        log.error(e)


def load_data(conn, federal_state, source_path):
    cur = conn.cursor()

    with open(source_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        if federal_state == 'hh':
            for row in reader:
                insert_row_hh(cur, row)
        elif federal_state == 'sh':
            for row in reader:
                insert_row_sh(cur, row)


@click.command()
@click.option('--env', '-e', type=str, required=True, help='Set your local dot env path')
@click.option('--state', '-S', type=str, required=True, help='Set destination state short name')
@click.option('--source', '-s', type=str, required=True, help='Set source path to your csv')
@click.option('--verbose', '-v', is_flag=True, help='Print more verbose output')
@click.option('--debug', '-d', is_flag=True, help='Print detailed debug output')
def main(env, source, state, verbose, debug):
    if debug:
        log.basicConfig(format='%(levelname)s: %(message)s', level=log.DEBUG)
    if verbose:
        log.basicConfig(format='%(levelname)s: %(message)s', level=log.INFO)
        log.info(f'set logging level to verbose')
    else:
        log.basicConfig(format='%(levelname)s: %(message)s')

    recursion_limit = sys.getrecursionlimit()
    log.info(f'your system recursion limit: {recursion_limit}')

    conn = connect_database(env)
    load_data(conn, state, Path(source))


if __name__ == '__main__':
    sys.excepthook = log_exceptions

    main()
