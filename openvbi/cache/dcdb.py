##\cache dcdb.py
#
# File cache of DCDB S3 data based on CSB REST API search results
#
# Copyright 2023 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import requests
from openvbi.cache import Cache

# format datetime value to ISO string (fixed to UTC)
def format_date_string(value: datetime | None) -> str | None:
    if value:
        return value.strftime('%Y-%m-%dT%H:%M:%SZ')
    return None

# Supported search parameters for CSB REST API
# Default last updated parameters are set to previous day of uploads. This is to account for a lag in publishing time between the
# REST API and S3 bucket. Currently, this lag time is 1 day.
# Time-based parameters should be specified ISO string format (%Y-%m-%dT%H:%M:%SZ)
# String-based parameters are all string equals queries, though this module can be extended to include string
#  contains queries if desired
@dataclass
class CSBRestApiSearchParameters:
    provider: List[str] = None
    trace_id: List[str] = None
    file_name: List[str] = None
    platform: List[str] = None
    last_updated_ge: datetime = datetime.now() - timedelta(days=2)
    last_updated_lt: datetime = datetime.now() - timedelta(days=1)
    start_time_lt: datetime = None
    start_time_ge: datetime = None
    end_time_lt: datetime = None
    end_time_ge: datetime = None
    file_size_lt: int = None
    file_size_ge: int = None
    
def download_object(bucket_path: str, cache_path: Path, item: dict) -> None:
    try:
        # convert filename to S3 object path
        filename = item["fileName"]

        filename_without_extension = filename.replace(".tar.gz", "")

        time_code = filename_without_extension.split("_", 2)[0]
        year = time_code[0:4]
        month = time_code[4:6]
        day = time_code[6:8]

        object_name = f"{filename_without_extension}_pointData.csv"

        object_path = f"{bucket_path}/{year}/{month}/{day}/{object_name}"

        # store file in a flat cache directory
        output_file_path = cache_path.joinpath(object_name)

        # users should remove a file from a cache directory if replacement is needed
        if output_file_path.exists():
            print(f"{output_file_path} already exists, skipping download")
            return
        
        # download object from S3
        print(f"downloading {object_path} to {output_file_path}")
        with requests.get(object_path, stream=True) as response:
            status_code = response.status_code
            # This should not typically happen, but can happen if an S3 object is either:
            # A) Removed
            # B) Not yet published
            if status_code != 200:
                raise RuntimeError(f"{object_path} download did not return 200 status, returned {status_code}")

            with open(output_file_path, 'wb') as output_file:
                for line in response.iter_lines():
                    if line:
                        output_file.write(line + b"\n")
        print(f"downloaded {object_path} to {output_file_path}")
    except Exception as e:
        print(f"file download failed for {object_path}: {e}")


class CSBRestAPICache(Cache):
    def __init__(self, dir: Path, bucket_path: str = 'https://noaa-dcdb-bathymetry-pds.s3.amazonaws.com/csb/csv', api_url: str = "https://ngdc.noaa.gov/ingest-external/index-service/api/v1/csb/index", max_concurrent_downloads: int = 5):
        self.dir = dir
        self._bucket_path = bucket_path # s3 root url
        self._api_url = api_url # CSB REST API index endpoint url
        self._max_concurrent_downloads = max_concurrent_downloads # maximum number of threads that can download from S3 at once

    def update(self, search_parameters: CSBRestApiSearchParameters) -> None:
        # establish thread pool for performing downloads in parallel
        # utilizing the executor in a 'with' block pauses the main thread until threads performing downloads have finished
        with ThreadPoolExecutor(max_workers=self._max_concurrent_downloads) as executor:
            self._iterate_pages(search_parameters, executor)

    def _perform_request(self, page: int, search_parameters: CSBRestApiSearchParameters, executor: ThreadPoolExecutor) -> Tuple[int, int]:
        print(f"submitting request to {self._api_url} for page {page}")

        # preparation of CSB REST API query parameters
        # parameters should be given as is unless they are datetimes, where they should be converted to ISO strings
        params = {
                "page": page,
                "itemsPerPage": 200, # CSB REST API's maximum number of items per page is 200

                "providerEquals": search_parameters.provider,
                "traceId": search_parameters.trace_id,
                "fileNameEquals": search_parameters.file_name,
                "platformEquals": search_parameters.platform,
                "lastUpdatedGe": format_date_string(search_parameters.last_updated_ge),
                "lastUpdatedLt": format_date_string(search_parameters.last_updated_lt),
                "endTimeGe": format_date_string(search_parameters.end_time_ge),
                "endTimeLt": format_date_string(search_parameters.end_time_lt),
                "startTimeGe": format_date_string(search_parameters.start_time_ge),
                "startTimeLt": format_date_string(search_parameters.start_time_lt)
            }

        body = requests.get(self._api_url, params=params).json()

        for item in body["items"]:
            # download file within thread pool
            executor.submit(download_object, self._bucket_path, self.dir, item)

        return body["page"], body["totalPages"]

    # loops through available pages of search results until current page reaches the end of available pages
    def _iterate_pages(self, search_parameters: CSBRestApiSearchParameters, executor: ThreadPoolExecutor) -> None:
        page = 1
        total_pages = None

        while total_pages is None or page <= total_pages:
            page, total_pages = self._perform_request(page, search_parameters, executor)
            page += 1