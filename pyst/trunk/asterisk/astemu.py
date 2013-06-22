import socket
from   signal import SIGTERM
from   os import fork, kill, waitpid
from   time import sleep

class Event(dict):
    """ Events are encoded as dicts with a header fieldname to
        content-list map. Normally (for all typical asterisk events) the
        content-list only has one element. For multiple elements
        multiple lines with the same header (but different content) are
        sent. This tests cases where asterisk events contain multiple
        instances of the same header.
        The key 'CONTENT' is special, it denotes text that is appended
        to an event (e.g. for testing the output of the command action)
    """
    sort_order = dict ((x, n) for n, x in enumerate
        (( 'Event'
         , 'Response'
         , 'Username'
         , 'Privilege'
         , 'Secret'
         , 'Command'
         , 'Channel'
         , 'ChannelState'
         , 'ChannelStateDesc'
         , 'CallerIDNum'
         , 'CallerIDName'
         , 'AccountCode'
         , 'Context'
         , 'Exten'
         , 'Reason'
         , 'Uniqueid'
         , 'ActionID'
         , 'OldAccountCode'
         , 'Cause'
         , 'Cause-txt'
        )))
    sort_order ['CONTENT'] = 100000

    def sort(self, x):
        return self.sort_order.get(x[0], 10000)

    def as_string(self, id):
        ret = []
        if 'Response' in self:
            self ['ActionID'] = [id]
        for k,v in sorted(self.iteritems(), key=self.sort):
            if k == 'CONTENT':
                ret.append(v)
            else :
                if isinstance(v, str):
                    ret.append (": ".join ((k, v)))
                else:
                    for x in v:
                        ret.append (": ".join ((k, x)))
        ret.append ('')
        ret.append ('')
        return '\r\n'.join (ret)

    @property
    def name(self):
        return self.get('Event','')

    @property
    def headers(self):
        return self

class AsteriskEmu(object):
    """ Emulator for asterisk management interface.
        Used for unittests of asterisk.manager.
        Now factored into a standalone module for others to use in
        unittests of programs that build on pyst's asterisk.manager.
        By default let the operating system decide the port number to
        bind to, resulting port is stored in self.port.
    """

    default_events = dict \
        ( Login =
            ( Event
                ( Response = ('Success',)
                , Message  = ('Authentication accepted',)
                )
            ,
            )
        , Logoff =
            ( Event
                ( Response = ('Goodbye',)
                , Message  = ('Thanks for all the fish.',)
                )
            ,
            )
        )

    def __init__(self, chatscript, port = 0):
        s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', port))
        s.listen(1)
        pid = fork()
        if not pid:
            # won't return
            self.asterisk_emu(s, chatscript)
        self.childpid = pid
        host, self.port = s.getsockname()
        s.close()

    def asterisk_emu(self, sock, chatscript):
        """ Emulate asterisk management interface on a socket.
            Chatscript is a dict of command names to event list mapping.
            The event list contains events to send when the given
            command is recognized.
        """
        while True:
            conn, addr = sock.accept()
            f = conn.makefile('rw')
            conn.close()
            f.write('Asterisk Call Manager/1.1\r\n')
            f.flush()
            cmd = lastid = ''
            try:
                for l in f:
                    if l.startswith ('ActionID:'):
                        lastid = l.split(':', 1)[1].strip()
                    elif l.startswith ('Action:'):
                        cmd = l.split(':', 1)[1].strip()
                    elif not l.strip():
                        for d in chatscript, self.default_events:
                            if cmd in d:
                                for event in d[cmd]:
                                    f.write(event.as_string(id = lastid))
                                    f.flush()
                                    if cmd == 'Logoff':
                                        f.close()
                                break
            except:
                pass
            sleep(10000) # wait for being killed

    def close(self):
        if self.childpid:
            kill(self.childpid, SIGTERM)
            waitpid(self.childpid, 0)
            self.childpid = None
