import datetime
import json
import responses

from openvbi.cache.dcdb import CSBRestAPICache, CSBRestApiSearchParameters

from tests.fixtures import temp_path

# test building of S3 object cache pertaining to CSB Rest API search results
@responses.activate
def test_csb_rest_api_cache(temp_path):
    s3_path = "https://localhost/s3/csb/csv"
    csb_rest_api_path = "https://localhost/csb/api"

    # simulate first request to CSB REST API (page 1)
    filename1 = "20230102003335666202_TEST.tar.gz"

    responses.add(responses.GET, csb_rest_api_path, body=json.dumps({
        "page": 1,
        "itemsPerPage": 1,
        "totalPages": 2,
        "items": [{
            "fileName": filename1
        }]
    }))

    content1 = "UNIQUE_ID,FILE_UUID,LON,LAT,DEPTH,TIME,PLATFORM_NAME,PROVIDER\n"

    file_uuid1 = filename1.replace(".tar.gz", "")

    for i in range(-90, 90):
        unique_id = f"UNIQUE_ID_{i}"
        platform = f"PLATFORM_NAME_{i}"
        provider = f"PROVIDER_{i}"
        iso = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        lon = i - 90
        lat = i
        depth = i * 100

        content1 += f"{unique_id},{file_uuid1},{lon},{lat},{depth},{iso},{platform},{provider}\n"

    responses.add(responses.GET, f'{s3_path}/2023/01/02/20230102003335666202_TEST_pointData.csv', body=content1)

    # simulate first request to CSB REST API (page 2)
    filename2 = "20240102003335666202_TEST.tar.gz"
    
    responses.add(responses.GET, csb_rest_api_path, body=json.dumps({
        "page": 2,
        "itemsPerPage": 1,
        "totalPages": 2,
        "items": [{
            "fileName": filename2
        }]
    }))

    content2 = "UNIQUE_ID,FILE_UUID,LON,LAT,DEPTH,TIME,PLATFORM_NAME,PROVIDER\n"

    file_uuid2 = filename2.replace(".tar.gz", "")

    for i in range(-90, 90):
        unique_id = f"UNIQUE_ID_{i}"
        platform = f"PLATFORM_NAME_{i}"
        provider = f"PROVIDER_{i}"
        iso = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        lon = i - 90
        lat = i
        depth = i * 100

        content2 += f"{unique_id},{file_uuid2},{lon},{lat},{depth},{iso},{platform},{provider}\n"

    responses.add(responses.GET, f'{s3_path}/2024/01/02/20240102003335666202_TEST_pointData.csv', body=content2)

    CSBRestAPICache(temp_path, bucket_path=s3_path, api_url=csb_rest_api_path).update(CSBRestApiSearchParameters())

    # assert that mocked s3 contents are downloaded to cache directory
    with open(temp_path.joinpath(f"{file_uuid1}_pointData.csv")) as f:
        assert content1 == f.read()

    with open(temp_path.joinpath(f"{file_uuid2}_pointData.csv")) as f:
        assert content2 == f.read()