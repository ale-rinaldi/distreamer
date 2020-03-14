FROM python:2.7-alpine

RUN apk add --no-cache esh && \
    addgroup -S distreamer && \
    adduser -S distreamer -G distreamer && \
    mkdir /distreamer && \
    chown distreamer:distreamer /distreamer

COPY distreamer.py /distreamer
COPY /General /distreamer/General
COPY /Inputs /distreamer/Inputs
COPY /Outputs /distreamer/Outputs
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/distreamer.conf.esh /distreamer/distreamer.conf.esh

USER distreamer
WORKDIR /distreamer
ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "distreamer.py" ]
