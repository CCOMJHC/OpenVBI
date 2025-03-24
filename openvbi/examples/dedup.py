import time
import pandas
import geopandas
import json
from openvbi.adaptors.generic_ascii import PreparsedASCIILoader
from openvbi.filters.deduplicate import deduplicate
import openvbi.core.metadata as md

def report_metadata(m: md.Metadata, tag: str) -> None:
    d = json.dumps(m.metadata(), indent=2)
    print(f'{tag}:')
    print(d)

startTime = time.perf_counter()
loader = PreparsedASCIILoader()
data = loader.load('/data/wibl-raw.N1K.csv')
endTime = time.perf_counter()
print(f'LoadData:             {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

print(data.depths)

report_metadata(data.meta, 'Before deduplication')

startTime = time.perf_counter()
dedup = deduplicate(verbose=True)
deduped_data = dedup.Execute(data)
endTime = time.perf_counter()
print(deduped_data.depths)
print(f'Deduplicate:          {1000*(endTime - startTime):8.3f} ms (started {startTime:.3f}, completed {endTime:.3f})')

report_metadata(deduped_data.meta, 'After deduplication')
