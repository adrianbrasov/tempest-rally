# Rally-Tempest-Tungsten
---
Title: Rally-Tempest-Tungsten
Author: Brasov Adrian Ioan
Footer: Copyright\ \textcopyright\ 2019, Juniper Networks, Inc.
---
## Download

~~~
git clone https://github.com/adrianbrasov/tempest-rally.git
~~~
---
## Configuration

- The Rally framework will build a deployment for the targeted OpenStack installation using a JSON file ( rally deployment create __--filename existing.json__ --name cloud)
- The file must be placed in the /data folder of the repo 
~~~json
{
    "openstack": {
        "auth_url": "http://controller:5000/v3/",
        "region_name": "RegionOne",
        "endpoint_type": "public",
        "admin": {
            "username": "admin",
            "password": "admin_user_secret",
            "tenant_name": "admin"
        },
        "https_insecure": false,
        "https_cacert": ""
    }
}
~~~
---
## Installation
- navigate to the repo folder
- build the Docker image
~~~
cd tempest-rally
docker build -t tempest-rally .
~~~
---

## Run
- The docker image is designed to be ran using Jenkins Pipeline Jobs
    ##### Jenkins Parameters:
    - **output_path** - string - local path where rally reports are saved
    - **image_name** - string - docker image name
    - **verifier** - string - rally verifier
    - **test_cases** - multi-line string - one test case per row
 - Run:
~~~bash
docker run --rm --name tempest_rally \
            -v ${output_path}:/output -e TEST_CASES=\"${test_cases}\" \
            ${image_name} /bin/bash -c \
            '/data/start.sh \
            cloud /data/existing.json ${verifier} '
~~~

