#!/bin/sh

esh /distreamer/distreamer.conf.esh > /distreamer/distreamer.conf
exec ${@}
