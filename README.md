pysigstream
===========

A simpler signal interface for python.

Signals are a pain. Once you register a signal every system call can be interrupted and you have to deal with it. Signals run asynchronously and you have to deal with that.

We need a better way to do it, luckily in Gnu/Linux this has been solved (there are routines in libc that allow you to make signals appear to come from a stream/file (the sort of thing that you can wait on with poll/select/epoll etc.). But python does not have support for this.

Therefore I have written this python library. It uses clib so will not work on all systems, however it does work on Gnu/Linux.

Hope it is useful.

©2013 Richard Delorenzi. Licence Gnu Gpl version 3, or later.
