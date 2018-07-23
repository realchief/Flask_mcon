import cStringIO
import os
import multiprocess as mp
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

import pycountry


class GeosFiller(object):
    """docstring for GeosFiller"""

    def __init__(self, db, username, password, host):
        super(GeosFiller, self).__init__()
        self.db = db
        self.username = username
        self.password = username
        self.host = host
        self.conn = psycopg2.connect(
            database=self.db,
            user=self.username,
            password=self.password,
            host=self.host
        )
        self.cur = self.conn.cursor()
        global global_last_id
        global_last_id = mp.Value('i', 0)

    def get_all_onesignal_user_countries_into_geos(self):
        global global_last_id

        engine = create_engine(
            "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
        connection = engine.raw_connection()
        cur = connection.cursor()

        cur.execute(
            "SELECT country, timezone FROM onesignal_users GROUP BY (country, timezone);")
        results = cur.fetchall()

        connection.commit()

        # remove results with None as Country alpha_2
        no_none_results = [tupl for tupl in results if tupl[0] is not None]

        # RESULTS DICT WITh TIMEZONE:
        # results_dict = { index: { "country": str(pycountry.countries.get(alpha_2=tupl[0]).name), "alpha_2": str(tupl[0]), "timezone": tupl[1] } for index, tupl in enumerate(no_none_results) }

        # RESULTS DICT WITHOUT TIMEZONE:
        results_dict = {
            index: {
                "country": str(
                    pycountry.countries.get(
                        alpha_2=tupl[0]).name), "alpha_2": str(
                    tupl[0])} for index, tupl in enumerate(no_none_results)}

        geos_df = pd.DataFrame.from_dict(results_dict, "index")

        geos_df.drop_duplicates(subset='alpha_2', keep="last", inplace=True)

        # USING TIMEZONE:
        # alpha_2_timezone_tuple = tuple(zip(tuple(geos_df["alpha_2"]), tuple(geos_df["timezone"])))
        # cur.execute('SELECT alpha_2, timezone FROM geos WHERE (alpha_2, timezone) IN {};'.format(alpha_2_timezone_tuple))
        # existing_alpha_2_timezone = cur.fetchall()
        # print(existing_alpha_2_timezone)

        cur.execute(
            'SELECT alpha_2 FROM geos WHERE alpha_2 IN {};'.format(
                tuple(
                    geos_df["alpha_2"])))
        existing_alpha_2 = [tup[0] for tup in cur.fetchall()]
        connection.commit()

        # remove existing rows from dataframe:
        geos_df = geos_df[~geos_df['alpha_2'].isin(existing_alpha_2)]

        # Get last geos id and compare to global_last_id.value
        cur.execute('SELECT MAX(id) FROM geos;')
        last_geos_id = cur.fetchone()[0]
        if last_geos_id is None:
            last_geos_id = 0
        if global_last_id.value < last_geos_id:
            global_last_id.value = last_geos_id

        # increment id on new geos
        try:
            geos_df.index = range(
                global_last_id.value + 1,
                len(geos_df) + global_last_id.value + 1)
        except Exception as error:
            print("THERE WAS AN EXEPTION ", error)

        print(geos_df)

        output = cStringIO.StringIO()

        try:
            # ignore the index
            geos_df.to_csv(
                output,
                sep='|',
                header=False,
                index=True,
                encoding='utf-8')

        except Exception as error:
            print('AN ERROR EXPORTING DATAFRAME TO CSV {}'.format(error))

        # jump to start of stream
        output.seek(0)
        contents = output.getvalue()

        # null values become ''
        try:
            cur.copy_from(output, 'geos', null="NULL", sep="|")
        except Exception as error:
            print('ERROR COPYING TO DATABASE {}'.format(error))

        connection.commit()

        cur.close()


if __name__ == "__main__":
    host = os.environ["PUSH_DB_HOST"]
    db = os.environ["PUSH_DB"]
    username = os.environ["PUSH_DB_USER"]
    password = os.environ["PUSH_DB_PASSWD"]

    # host = "localhost"
    # db = "pushengine"
    # username = "postgres"
    # password = "postgres"
    gf = GeosFiller(db, username, password, host)
    gf.get_all_onesignal_user_countries_into_geos()


# run the following commands in postgres:

# CREATE TABLE geos ( id serial PRIMARY KEY, name varchar(255) NOT NULL,
# alpha_2 char(2) NOT NULL, UNIQUE (name), UNIQUE (alpha_2));

# CREATE TABLE message_categories ( id serial PRIMARY KEY, name
# varchar(255) NOT NULL, UNIQUE (name));

# CREATE TABLE frequencies ( id serial PRIMARY KEY, interval varchar(255) NOT NULL, selected BOOLEAN DEFAULT FALSE, UNIQUE (interval));
# CREATE TABLE geos_scheduled_message (geo_id int REFERENCES geos (id) ON
# UPDATE CASCADE ON DELETE CASCADE, scheduled_message_id int REFERENCES
# scheduled_message (id) ON UPDATE CASCADE, UNIQUE (geo_id,
# scheduled_message_id));

# INSERT INTO message_categories(name) VALUES('Dating');
# INSERT INTO message_categories(name) VALUES('General');
# INSERT INTO message_categories(name) VALUES('Casino');
# INSERT INTO message_categories(name) VALUES('Utility');
# INSERT INTO message_categories(name) VALUES('Gaming');
# INSERT INTO message_categories(name) VALUES('Test 1');
# INSERT INTO message_categories(name) VALUES('Test 2');
# INSERT INTO message_categories(name) VALUES('Test 3');
# INSERT INTO message_categories(name) VALUES('Test 4');
# INSERT INTO message_categories(name) VALUES('Test 5');
# INSERT INTO frequencies(interval) VALUES('Once');
# INSERT INTO frequencies(interval, selected) VALUES('Daily', 'TRUE');
