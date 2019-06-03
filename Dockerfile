FROM ubuntu

RUN apt-get update && apt-get install --yes sudo python python-pip vim wget git git-core tar && \
    pip install --upgrade pip 

WORKDIR /tmp

RUN wget https://github.com/openstack/rally/archive/1.5.1.tar.gz &&\
    gzip -d /tmp/1.5.1.tar.gz && \
    tar -xvf /tmp/1.5.1.tar && \
    /tmp/rally-1.5.1/install_rally.sh --target /rally_inst &&\
    git clone https://git.openstack.org/openstack/tempest &&\
    pip install tempest &&\
    /bin/bash -c " . /rally_inst/bin/activate; pip install rally-openstack; \
    rally verify create-verifier --type tempest --name tempest-verifier --source /tmp/tempest " 

ADD data /data