#!/bin/bash
set -e

# Get the putS3 function
source $HOME/.bashrc

SRC=$(pwd)  # run from project source folder
APP=${SRC##*/}

CME_HW_PN=1500-006

# Increment VERSION build number; the '123' in 1.0.0-123
VERSION=$(<${SRC}/VERSION)
IFS='-' read -ra PARTS <<< "${VERSION}"
BUILD_NUMBER=${PARTS[1]}
((BUILD_NUMBER++))
$(echo "${PARTS[0]}-${BUILD_NUMBER}" > ${SRC}/VERSION)
VERSION=$(<${SRC}/VERSION)

BASENAME=${CME_HW_PN}-v${VERSION}-SWARE-CME_HW

PACKAGE=${BASENAME}.tgz
DOCKER_PKG=${BASENAME}.pkg.tgz
DOCKER_NAME=cmehw:${VERSION}

# Stage 1.  Build and publish base (recovery) package
#echo
#echo "    Stage 1.  Building and publishing base package: ${PACKAGE} ..."
#echo

# Build base image
#build/build.sh 

#echo
#echo "    ... done building."
#echo

# Publish base image to S3
#cd build
#putS3 ${PACKAGE} Cme
#cd ..

#echo
#echo "    ... done publishing."
#echo


# Stage 1.  Build and publish docker package
echo
echo "    Stage 1.  Building and publishing docker package: ${DOCKER_PKG} ..."
echo "        a) Building docker image binaries ..."
echo

docker run --rm -v ${SRC}:/root/app cme-build "build/build.sh .docker"

echo
echo "    ... done building docker image binaries."
echo "        b) Building docker image ..."
echo

# Use docker package binaries and build docker app image
cd build
docker build -t ${DOCKER_NAME} --build-arg version=${VERSION} .

echo
echo "    ... done building docker image."
echo "        c) Saving docker image into package ..."
echo

# Save docker image to package
docker save ${DOCKER_NAME} | gzip > ${DOCKER_PKG}

echo
echo "    ... done saving docker image into package."
echo "        d) Publishing docker package ..."
echo

putS3 ${DOCKER_PKG} Cme
cd ../

echo
echo "    ... All done!"
echo
