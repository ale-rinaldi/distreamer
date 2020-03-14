# DiStreamer 2.0
DiStreamer is a simple Python script specifically designed to stream audio over unstable connections, making its best to avoid interruptions in sound. It works by splitting audio data into a set of fragments of a given size.
It is possible to run an unlimited number of istances of DiStreamer concurrently, each with a different config file.
For an instance to run you need to set an INPUT and OUTPUT module. The INPUT module will generate the data fragments, and the OUTPUT will serve it in the way you like.

A typical use case consists of two PCs (A and B) linked by an unstable connection. A has a ShoutCast server, and B an audio player.
In this case, we run DiStreamer on PC A with ShoutcastClient as INPUT and DiStreamerServer as OUTPUT. The INPUT reads data from ShoutCast and splits it into fragments, while the OUTPUT serves those fragments in DiStreamer's own format.
On PC B we'll have DiStreamer running with DiStreamerClient as INPUT and ShoutcastServer as OUTPUT. The INPUT gets the fragments from DiStreamer Server on PC A, and the OUTPUT emulates a ShoutCast server the audio player will connect to.
If PC A or B loose network connectivity for less than the total buffer time, no one will notice it. PC B can even change IP without any problem!

There are various other INPUT and OUTPUT modules to use in the near future, for example there is a ShoutcastServer INPUT to avoid using ShoutCast at all, and a Reverse DiStreamer Server and Client to let a client push fragments to the server. Refer to `Inputs` and `Outputs` folders for a complete list of modules.
If you have some good idea for an INPUT or OUTPUT module, and you like coding, PLEASE contribute!

*WARNING*: as usual, in the open source world, this software is offered without any warranty. Feel free to write me if you have any issue and I'll be glad to help if I can.

# Usage
Unfortunately there is not much documentation about how to use DiStreamer at the moment: the project was born to be used internally in our radio station ([Radio 2.0 - Bergamo in aria](https://www.radioduepuntozero.it)), and I didn't put so much effort in documenting it. My fault, sorry. If you're brave enough, you can try to figure out how it works by reading the `distreamer.template.conf` file, it has some comments that might help.

If you're really interested in running DiStreamer and you need some hints to get started, just contact me or open a issue, I'll be glad to help!

## Docker
Docker is the recommended way to run DiStreamer. You can configure it using environment variables:
- variables starting with `DS_GENERAL_` are put in the `GENERAL` configuation section
- variables starting with `DS_INPUT_` are put in the `INPUT` configuration section
- variables starting with `DS_OUTPUT_` are put in the `OUTPUT` configuration section

For example, setting `DS_GENERAL_OUTPUTLEVEL=1` will produce:
```ini
[GENERAL]
OUTPUTLEVEL=1
```

A full list of all the available options, with some commends about what they do, can be found in the `distreamer.template.conf` in the GitHub repository.

Alternatively, you can mount a directory containing a `distreamer.conf` file into `/distreamer/conf`. This way, the config file won't be generated from the environment variables.

## Without docker
The file to run is distreamer.py and it accepts only one argument: a path to a configuration file. If no path is given, it will use "distreamer.conf" in the current directory.
So, to use DiStreamer you just:
- Install Python 2.7
- Download DiStreamer
- Rename distreamer.template.conf in distreamer.conf
- Edit distreamer.conf following the comments
- Launch "python distreamer.py" in a shell
