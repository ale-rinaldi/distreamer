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
The file to run is distreamer.py and it accepts only one argument: a path to a configuration file. If no path is given, it will use "distreamer.conf" in the current directory.
So, to use DiStreamer you just:
- Install Python 2.7
- Download DiStreamer
- Rename distreamer.template.conf in distreamer.conf
- Edit distreamer.conf following the comments
- Launch "python distreamer.py" in a shell
