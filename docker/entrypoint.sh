#!/bin/sh

if [ ! -f "/distreamer/conf/distreamer.conf" ]; then
    esh /distreamer/distreamer.conf.esh > /distreamer/conf/distreamer.conf
fi

exec ${@}
