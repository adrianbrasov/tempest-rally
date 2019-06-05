#!/bin/bash

name=$1
file=$2
pattern=$3
verifier=$4

#functions
create_deployment() {
    rally deployment create --name $name --filename $file 
}

verify_start() {
    if [ -z $pattern ]
      then 
        uuid=`rally verify start --detailed| \
        tee /dev/stderr | grep UUID |tail -1 | awk -F '[=)]' '{print $2}'`
    else 
        uuid=`rally verify start --pattern $pattern --detailed | \
        tee /dev/stderr | grep UUID |tail -1 | awk -F '[=)]' '{print $2}'`
    fi
}

# source rally
. /rally_inst/bin/activate

# create deploymment 
create_deployment

# source deployment 
source ~/.rally/openrc

# select verifier
rally verify use-verifier --id $verifier

# start verification
verify_start

#generate report
rally verify report --to /output/report_$uuid.html --uuid $uuid --type html
