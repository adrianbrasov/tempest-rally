#!/bin/bash

. /rally_inst/bin/activate; 
uuid=`rally verify create-verifier --type tempest --name tungsten-tempest --source /Repos/tungsten-tempest/ | grep UUID | tail -1 | awk -F '[=)]' '{print $2}'`
echo $uuid ;\
cp -rp /data/tungsten-stestr.conf /root/.rally/verification/verifier-$uuid/repo/.stestr.conf 
rally verify create-verifier --type tempest --name tempest-verifier --source /Repos/tempest 
rally verify create-verifier --type tempest --name patrole-verifier --source /Repos/patrole/ 