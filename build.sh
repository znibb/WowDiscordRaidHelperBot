#!/bin/bash

user=znibb
name=raidhelper:latest

# Remove stopped container
docker container rm $(docker ps -a | grep $user/$name | awk '{print $1}') > /dev/null 2>&1

# Delete old image to prevent dangling image
docker image rm $user/$name > /dev/null 2>&1

# Rebuild image
docker build --no-cache -t $user/$name .