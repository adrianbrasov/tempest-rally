FROM ubuntu

ADD Repos /Repos
ADD data /data

RUN apt-get update && apt-get install --yes sudo python python-pip vim wget git git-core tar && \
    pip install --upgrade pip 

RUN /Repos/rally-1.5.1/install_rally.sh --target /rally_inst

WORKDIR /Repos
RUN git clone https://git.openstack.org/openstack/tempest &&\
    git clone https://git.openstack.org/openstack/patrole &&\
    git clone https://github.com/tungstenfabric/tungsten-tempest

WORKDIR /Repos/tempest
RUN pip install -e .

WORKDIR /Repos/patrole
RUN  pip install -e .

WORKDIR /Repos/tungsten-tempest/
RUN pip install -e .

RUN pip install mock &&\
    /bin/bash -c ". /rally_inst/bin/activate; \
    pip install rally-openstack; \
    pip install mock; "

RUN /bin/bash /data/tempest-verifiers.sh
