import cStringIO
import os
import multiprocess as mp
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

import pycountry


class CampaignRuleConstraintMigrator(object):
    """docstring for CampaignRuleConstraintMigrator"""

    def __init__(self, db, username, password, host):
        super(CampaignRuleConstraintMigrator, self).__init__()
        self.db = db
        self.username = username
        self.password = password
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

    def migrate_constraints(self):
        global global_last_id

        engine = create_engine(
            "postgresql://{0}:{1}@{2}/{3}".format(self.username, self.password, self.host, self.db))
        connection = engine.raw_connection()
        cur = connection.cursor()

        cur.execute("SELECT * FROM campaign_rule;")
        results = cur.fetchall()


        connection.commit()

        # RESULTS DICT:
        results_dict = {
            index: {
                "id": tupl[0], 
                "campaign_id": tupl[1],
                "y_metric_gtlt": tupl[2],
                "y_metric": tupl[3],
                "y_metric_amount": tupl[4],
                "x_metric": tupl[5],
                "x_metric_amount": tupl[6],
                "x_metric_gtlt": tupl[7],
                "period": tupl[8],
                "action": tupl[9],
                "status": tupl[10]
                } for index, tupl in enumerate(results)}

        results_df = pd.DataFrame.from_dict(results_dict, "index")

        y_constraints_df = results_df[['id','y_metric', 'y_metric_amount','y_metric_gtlt']].copy()
        y_constraints_df.columns = ['campaign_rule_id','metric', 'value','operator']
        x_constraints_df = results_df[['id','x_metric', 'x_metric_amount', 'x_metric_gtlt']].copy()
        x_constraints_df.columns = ['campaign_rule_id','metric', 'value','operator']
        constraints_df = y_constraints_df.append(x_constraints_df, ignore_index=True)
        constraints_df['conjunction'] = None

        constraints_df['metric'] = map(lambda x: x.upper(), constraints_df['metric'])

        existing_campaign_rule_ids = []
        for index, row in constraints_df.iterrows():
            if row['campaign_rule_id'] not in existing_campaign_rule_ids:
                existing_campaign_rule_ids.append(row['campaign_rule_id'])
            else:
                constraints_df.loc[index, 'conjunction'] = 'and'
            if row['operator'] == 'lt':
                constraints_df.loc[index, 'operator'] = '<'
            elif row['operator'] == 'gt':
                constraints_df.loc[index, 'operator'] = '>'


        # Get last rule_constraint id and compare to global_last_id.value
        cur.execute('SELECT MAX(id) FROM rule_constraint;')
        last_rule_constraints_id = cur.fetchone()[0]
        if last_rule_constraints_id is None:
            last_rule_constraints_id = 0
        if global_last_id.value < last_rule_constraints_id:
            global_last_id.value = last_rule_constraints_id

        # increment id on new geos
        try:
            constraints_df.index = range(
                global_last_id.value + 1,
                len(constraints_df) + global_last_id.value + 1)
        except Exception as error:
            print("THERE WAS AN EXEPTION ", error)

        output = cStringIO.StringIO()

        try:
            # ignore the index
            constraints_df.to_csv(
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
            cur.copy_from(output, 'rule_constraint', null="NULL", sep="|")
        except Exception as error:
            print('ERROR COPYING TO DATABASE {}'.format(error))

        cur.execute('ALTER TABLE campaign_rule DROP COLUMN y_metric, DROP COLUMN y_metric_gtlt, DROP COLUMN y_metric_amount, DROP COLUMN x_metric, DROP COLUMN x_metric_gtlt, DROP COLUMN x_metric_amount;')

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
    crcm = CampaignRuleConstraintMigrator(db, username, password, host)
    crcm.migrate_constraints()

# DROP TABLE rule_constraint;

# CREATE TABLE rule_constraint (id serial PRIMARY KEY, campaign_rule_id int REFERENCES campaign_rule (id) ON DELETE CASCADE ON UPDATE CASCADE, metric varchar(13) NOT NULL, value decimal NOT NULL, operator varchar(5) NOT NULL, conjunction varchar(10));


# ALTER TABLE campaign_rule DROP COLUMN period, DROP COLUMN action, DROP COLUMN status, DROP COLUMN traffic_source;
# ALTER TABLE campaign_rule ADD COLUMN period int DEFAULT 3, ADD COLUMN action varchar(10) DEFAULT 'Pause', ADD COLUMN status BOOLEAN DEFAULT true, ADD COLUMN traffic_source varchar(100);


# INSERT INTO campaign_rule(campaign_id, y_metric_gtlt, y_metric, y_metric_amount, x_metric, x_metric_amount, x_metric_gtlt, period, action, status, traffic_source) VALUES(1, 'lt', 'cv', 1, 'visits', 100, 'gt', 7, 'Pause', true, 'zeropark');

# INSERT INTO rule_constraint(campaign_rule_id, metric, value, operator, conjunction) VALUES(53, 'ROI', 99, '<', NULL);
# INSERT INTO rule_constraint(campaign_rule_id, metric, value, operator, conjunction) VALUES(53, 'CV', 2, '==', 'and');
