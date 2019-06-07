#!/bin/bash

name=$1
file=$2
verifier=$3
test_cases=/data/test_cases.txt

#functions
create_deployment() {
    rally deployment create --name $name --filename $file 
}

verify_start() {
    if [ `wc -w $test_cases | awk '{print $1}'` -lt 1 ]
      then 
        uuid=`rally verify start --detailed| \
        tee /dev/stderr | grep UUID |tail -1 | awk -F '[=)]' '{print $2}'`
    else 
        uuid=`rally verify start --load-list $test_cases --detailed | \
        tee /dev/stderr | grep UUID |tail -1 | awk -F '[=)]' '{print $2}'`
    fi
}

#populate test_cases file from env
echo "$TEST_CASES" > /data/test_cases.txt

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
