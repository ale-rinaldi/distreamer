# DiStreamer 1.0.4
DiStreamer is a simple Python script specifically designed to stream audio over unstable connections, making its best to avoid "holes" in sound. To achieve this, it splits data into a set of pieces of a given size.  
It is composed by a client and a server.  

*WARNING*: this is pre-pre-pre-pre-pre-pre-release software, so....... well, you already know it ;) write me if you have any issue and I'll be glad to help if I have time, but without any warranty.

# DiStreamer Server
This reads data from a ShoutCast Server and splits it into several blocks. It will then serve them to the clients using HTTP.  

# DiStreamer Client
This will get the parts from the server and reassembles them into a readable stream. It will keep retrying if it fails to download some parts.  
It will then emulate a ShoutCast server so that a player can get a reliable audio stream from it.

# Usage
Both the client and the server accepts only one argument: a path to a configuration file. If no path is given, it will use "distreamer.conf" in the current directory.
So, to use DiStreamer you just:
- Install Python 2.7
- Download DiStreamer
- Rename distreamer.template.conf in distreamer.conf
- Edit distreamer.conf following the comments
- Start distreamer-client or distreamer-server