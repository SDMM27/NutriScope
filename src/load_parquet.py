INPUT_FILE = "data/extracts"
from os import listdir
from os.path import isfile, join
import pyarrow.parquet, pyarrow.csv, io

try:
    import psycopg
except ImportError:
    from pip._internal import main as pip
    pip(['install', '--user', 'psycopg'])
    import psycopg

def load_file(file_name):
    print(" "*10, "read file")
    buf = io.BytesIO()
    table = pyarrow.parquet.read_table(f"{INPUT_FILE}/{file_name}")
    print(" "*10, "write csv")
    pyarrow.csv.write_csv(table, buf, pyarrow.csv.WriteOptions(include_header=False, delimiter=','))
    buf.seek(0)

    print(" "*10, "copy csv into the SQL")
    with connection.cursor().copy("""COPY "importparquet" ({cols}) FROM STDIN WITH (FORMAT CSV)""".format(cols=','.join(table.column_names))) as copy:
        copy.write(buf.getvalue())

    print(" "*10, "close")
    connection.commit()
    connection.close()
    buf.close()

connection = psycopg.connect(host='localhost', port='5432', dbname='nutriscope', user='postgres', password='postgres')

onlyfiles = [f for f in listdir(INPUT_FILE) if isfile(join(INPUT_FILE, f))]

for file in onlyfiles:
    print (f"STARTING TO LOAD : {file}")
    load_file(file)
    print ("---"*20)
