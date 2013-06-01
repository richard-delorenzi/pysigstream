#!/usr/bin/python

import ctypes as _ctypes
import os as _os
import struct as _struct

class status:
    """
    read the signal status, not all values are valid for all signo:
    see: http://www.kernel.org/doc/man-pages/online/pages/man2/signalfd.2.html
    section The signalfd_siginfo structure
    """
    _buf=None

    #Magic numbers
    class _Indexes:
        _num32=12
        _num64=4

        ( signo,
          errno,
          code,
          pid,     
          uid,
          fd,
          tid,
          band,
          overren,
          trapno,
          status,
          int
          )=range(0,_num32)

        ( ptr,
          utime,
          stime,
          addr
          )=range(2*0+_num32, 
                  2*_num64+_num32, 
                  2)

    #Magic numbers
    class _ChildCodes:
        _numCodes=6
        ( exited,
          killed,
          dumped,
          traped,
          stopped,
          continued
          )=range(0+1,_numCodes+1)

    def _int32(self,index):
        return _struct.unpack("=l",self._buf[index*4:index*4+4])[0]

    def _uint32(self,index):
        return _struct.unpack("=L",self._buf[index*4:index*4+4])[0]

    def _int64(self,index):
        return _struct.unpack("=q",self._buf[index*4:index*4+8])[0]

    def _uint64(self,index):
        return _struct.unpack("=Q",self._buf[index*4:index*4+8])[0]

    def signo(self):
        return self._uint32(self._Indexes.signo)

    def code(self):
        return self._int32(self._Indexes.code)

    def userTime(self):
        return self._uint64(self._Indexes.utime)
    
    def systemTime(self):
        return self._uint64(self._Indexes.stime)

    def status(self):
        return self._int32(self._Indexes.status)

    def has_childExited(self):
        return (
            self.signo() == signal.SIGCHLD      and 
            self.code == self._ChildCode.exited )

    def uid(self):
        return self._uint32(self._Indexes.uid)

    def pid(self):
        return self._uint32(self._Indexes.pid)

class FileHandle:
    """this is what new returns
       you need to pass it to the register method of objects of:
       select.poll() or select.select() or select.epoll()
       and
       Handlers()
    """

    _fd=None
    
    def fileno(self):
        """
        return: filediscriptor, for use my select/poll/epoll
        """
        return self._fd

    def read(self):
        """
        when poll/select etc says you can, then read with this
        return: status object
        """
        Result=status()
        Result._buf=_os.read(self._fd,_Helper()._sigMsgSize)
        return Result

class _Helper:
    #Magic numbers
    _sigMaskBufSize=128
    _sigMsgSize=128
    _SIG_BLOCK=0

    _libc = _ctypes.CDLL("libc.so.6")

    def _Mask(self,signalList):
        #signalList: a list of signals, signal.SIG... e.g. signal.SIGHUP
        #returns: an object for use in ?????
        #returns: None if bad signal passed
        
        buf=_ctypes.create_string_buffer(0,self._sigMaskBufSize)
        ret=self._libc.sigemptyset(buf)
        assert(ret==0)

        for sig in signalList:
            ret=self._libc.sigaddset(buf,sig)
            if(ret!=0):
                return None
            
        return buf

    def _block(self,sigMask):
        #block signals, 
        #sigMask: use _sigMask to create
        
        ret=self._libc.sigprocmask(self._SIG_BLOCK,sigMask,None)
        assert(ret==0)

    def _newFd(self,sigMask):
        #create a new filediscriptor
        #return filediscriptor, for use my select/poll/epoll
        #sigMask: use _sigMask to create
        
        sigfd=self._libc.signalfd(-1,sigMask,0)
        #assert(sigfd != -1) #:todo:handle me
        handle= FileHandle()
        handle._fd=sigfd
        return handle

def new(signalList):
    """
    create a new handle
    return: FileHandle object
    return: None if invalid mask
    signalList: a list of signals, as defined in package signal e.g. signal.SIGHUP
    """
    helper=_Helper()

    mask=helper._Mask(signalList)
    if mask == None:
        return None
    else:
        helper._block(mask)
        return helper._newFd(mask)

class Handlers:
    """
    register fileHandles and handler procedures
    then ask me to handle them following a poll/select/epoll
    """

    _handlers=dict()
    
    def register(self,fileHandle,handler):
        """
        fileHandle: object implementing fileno() where 
           fileno returns a unix file descriptor.
        handler: a procedure(file,flags) where flags 

        note:  poll.poll() returns (fileno,flags)
        """
        self._handlers[fileHandle.fileno()]=(fileHandle,handler)
        
    def handle(self,fileno,flags):
        """
        After registering some handlers, with register
        call this with the two values that came out of poll.poll()
        and it will call your handlers for you.
        """
        handler=self._handlers[fileno]
        handler[1](handler[0],flags)

if __name__ == '__main__':
    #example of how to use

    import select
    import os
    import sys
    import signal

    import sigStream as sigStream

    class Class:
        def handleStdin(self,file,flags):
            ch=os.read(file.fileno(),1) #???
            sys.stdout.write( ch )
            sys.stdout.flush()

        def handleSig(self,file,flags):
            sys.stdout.write( "We got Signal\n" )
            stat=file.read()
            print "type: "     + str(stat.signo())
            print "pid: "      + str(stat.pid())
            print "code: "     + str(stat.code())
            print "Status: "   + str(stat.status())
            sys.stdout.flush()

            if stat.signo() == signal.SIGALRM:
                os.kill(os.getpid(),signal.SIGCHLD)

        def worker(self):
            poller = select.poll()
            sigFile=sigStream.new([signal.SIGCHLD,signal.SIGALRM])
            poller.register(sigFile,   select.EPOLLIN)
            poller.register(sys.stdin, select.EPOLLIN)
            
            signal.setitimer(signal.ITIMER_REAL, 2, 2)
            
            handlers=sigStream.Handlers()
            handlers.register(sigFile,   self.handleSig)
            handlers.register(sys.stdin, self.handleStdin)        

            print "Worker turn on"
            while True:
                for fd, flags in poller.poll():
                    handlers.handle(fd,flags)

    Class().worker()

        
