#!/bin/bash

kubectl create job --from=cronjob/mysql-backup-s3 manual-backup-$(date +%s) --overrides='{"spec":{"template":{"spec":{"containers":[{"name":"backup","env":[{"name":"MANUAL_TRIGGER","value":"true"}]}]}}}}'