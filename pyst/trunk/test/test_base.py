import sys
import socket
import unittest
from   signal import SIGTERM
from   asterisk.manager import Manager
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
    sort_order = dict \
        ( Response =     10
        , Username =     20
        , Secret   =     30
        , Command  =     30
        , ActionID =    100
        , CONTENT  = 100000
        )

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
                for x in v:
                    ret.append (": ".join ((k, x)))
        ret.append ('')
        ret.append ('')
        return '\r\n'.join (ret)

class Test_Manager(unittest.TestCase):
    """ Test the asterisk management interface.
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

    def asterisk_emu(self, sock, chatscript):
        """ Emulate asterisk management interface on a socket.
            Chatscript is a dict of command names to event list mapping.
            The event list contains events to send when the given
            command is recognized.
        """
        while True:
            conn, addr = sock.accept()
            f = conn.makefile('r')
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

    def setup_child(self, chatscript):
        s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        s.bind (('localhost', 0))
        s.listen(1)
        pid = fork()
        if not pid:
            # won't return
            self.asterisk_emu(s, chatscript)
        self.childpid = pid
        host, self.port = s.getsockname()
        s.close()

    def close(self):
        if self.manager:
            self.manager.close()
            self.manager = None

    def setUp(self):
        self.manager  = None
        self.childpid = None
        self.events   = []

    def tearDown(self):
        self.close()
        if self.childpid:
            kill(self.childpid, SIGTERM)
            waitpid(self.childpid, 0)
            self.childpid = None

    def handler(self, event, manager):
        self.events.append(event)

    def run_manager(self, chatscript):
        self.setup_child(chatscript)
        self.manager = Manager()
        self.manager.connect('localhost', port = self.port)
        self.manager.register_event ('*', self.handler)

    def compare_result(self, r_event, event):
        for k in event:
            if k == 'CONTENT':
                self.assertEqual(r_event.data, event ['CONTENT'])
            else:
                self.assertEqual(r_event[k], event[k][0])

    def test_login(self):
        self.run_manager({})
        r = self.manager.login('account', 'geheim')
        self.compare_result(r, self.default_events['Login'][0])
        self.close()
        self.assertEqual(self.events, [])

    def test_command(self):
        d = dict
        events = dict \
            ( Command =
                ( Event
                    ( Response  = ('Follows',)
                    , Privilege = ('Command',)
                    , CONTENT   = 
"""Channel              Location             State   Application(Data)
lcr/556              s@attendoparse:9     Up Read(dtmf,,30,noanswer,,2)    
1 active channel
1 active call
372 calls processed
--END COMMAND--\r
"""
                    )
                ,
                )
            )
        self.run_manager(events)
        r = self.manager.command ('core show channels')
        self.assertEqual(self.events, [])
        self.compare_result(r, events['Command'][0])

    def test_redirect(self):
        d = dict
        events = dict \
            ( Redirect =
                ( Event
                    ( Response  = ('Success',)
                    , Message   = ('Redirect successful',)
                    )
                ,
                )
            )
        self.run_manager(events)
        r = self.manager.redirect \
            ('lcr/556', 'generic', 'Bye', context='attendo')
        self.assertEqual(self.events, [])
        self.compare_result(r, events['Redirect'][0])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest (unittest.makeSuite (Test_Manager))
    return suite

if __name__ == '__main__':
    unittest.main()

