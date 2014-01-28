#!/bin/bash

APP_HOME=$HOME/generic-rest-service

cd $APP_HOME
source env/bin/activate

exec pserve production.ini 2>&1
