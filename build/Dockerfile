# This docker is used as the Cme-hw application layer.
#
# The Cme-hw application requires root access to hardware, memory
# and a shared /data location on the docker host as well as a link
# to the cme-mc (running) container.  To provide them,
# run this docker image with the following command:
#
#	$ docker run --rm \
#		--device=/dev/spidev0.0:/dev/spidev0.0 \
#		--device=/dev/spidev0.1:/dev/spidev0.1 \
#		--device=/dev/mem:/dev/mem \
#		--privileged \
#		--name cme-hw \
#		-v /data:/data \
#		cmehw:0.1.0

# Uses our cme-base docker image
FROM cme-base

LABEL maintainer "James Brunner <james.brunner@smithsmicrowave.com>"

# Pass the VERSION at docker build (docker build --build-arg version=1.0.0-99)
ARG version

# Add the application binaries - these must have been built for the cme-base docker!
ADD 1500-006-v$version-SWARE-CME_HW.docker.tgz .

# Install cme app using pip and built wheels
RUN pip install --no-index -f wheelhouse cmehw
RUN rm -rf wheelhouse/

CMD ["cmehw"]
