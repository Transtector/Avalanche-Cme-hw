#!/bin/sh
set -e

if [ "$1" = 'memcached' ]; then
	chown -R memcached .
	exec su-exec memcached "$@"
fi

exec "$@"
