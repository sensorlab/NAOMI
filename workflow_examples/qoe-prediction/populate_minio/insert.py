import pandas as pd
import datetime
from minio import Minio
from io import StringIO, BytesIO
import gzip

# Placeholder credentials for MinIO
MINIO_ENDPOINT = '193.2.205.63:30085'
MINIO_ACCESS_KEY = 'minio'
MINIO_SECRET_KEY = 'miniostorage'
MINIO_BUCKET_NAME = 'raybuck'

class INSERTDATA:
    def __init__(self):
        self.minio_client = Minio(MINIO_ENDPOINT,
                                  access_key=MINIO_ACCESS_KEY,
                                  secret_key=MINIO_SECRET_KEY,
                                  secure=False)  # Change to True if using HTTPS

def explode(df):
     for col in df.columns:
             if isinstance(df.iloc[0][col], list):
                     df = df.explode(col)
             d = df[col].apply(pd.Series)
             df[d.columns] = d
             df = df.drop(col, axis=1)
     return df


def jsonToTable(df):
     df.index = range(len(df))
     cols = [col for col in df.columns if isinstance(df.iloc[0][col], dict) or isinstance(df.iloc[0][col], list)]
     if len(cols) == 0:
             return df
     for col in cols:
             d = explode(pd.DataFrame(df[col], columns=[col]))
             d = d.dropna(axis=1, how='all')
             df = pd.concat([df, d], axis=1)
             df = df.drop(col, axis=1).dropna()
     return jsonToTable(df)


def time(df):
     df.index = pd.date_range(start=datetime.datetime.now(), freq='10ms', periods=len(df))
     df['measTimeStampRf'] = df['measTimeStampRf'].apply(lambda x: str(x))
     return df

def populatedb(N):
    df = pd.read_json('cell.json.gz', lines=True)
    df = df[['cellMeasReport']].dropna()
    df = jsonToTable(df)
    df = time(df)

    # Duplicate the dataframe N times
    df = pd.concat([df]*N, ignore_index=True)

    # Save dataframe to a temporary CSV file
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    # Upload CSV data to MinIO
    db = INSERTDATA()
    csv_bytes = BytesIO(csv_data.encode('utf-8'))
    db.minio_client.put_object(MINIO_BUCKET_NAME, f'qoe_data/liveCell-x{N}.csv', csv_bytes, len(csv_data))

# Call the function with the desired multiplier
populatedb(1)
# populatedb(10)
# populatedb(100)
