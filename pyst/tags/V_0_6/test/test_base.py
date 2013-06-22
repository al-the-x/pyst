import sys
import socket
import unittest
from   asterisk.manager import Manager
from   asterisk.compat import Queue
from   asterisk.astemu import Event, AsteriskEmu

class Test_Manager(unittest.TestCase):
    """ Test the asterisk management interface.
    """

    default_events = AsteriskEmu.default_events

    def close(self):
        if self.manager:
            self.manager.close()
            self.manager = None
        self.astemu.close()

    def setUp(self):
        self.manager  = None
        self.childpid = None
        self.events   = []
        self.evcount  = 0
        self.queue    = Queue()

    def tearDown(self):
        self.close()

    def handler(self, event, manager):
        self.events.append(event)
        self.queue.put(self.evcount)
        self.evcount += 1

    def run_manager(self, chatscript):
        self.astemu = AsteriskEmu (chatscript)
        self.port = self.astemu.port
        self.manager = Manager()
        self.manager.connect('localhost', port = self.port)
        self.manager.register_event ('*', self.handler)

    def compare_result(self, r_event, event):
        for k, v in event.iteritems():
            if k == 'CONTENT':
                self.assertEqual(r_event.data, v)
            elif isinstance(v, str):
                self.assertEqual(r_event[k], v)
            else:
                self.assertEqual(r_event[k], v[-1])
                self.assertEqual(sorted(r_event.multiheaders[k]),
                    sorted(list(v)))

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

    def test_originate(self):
        d = dict
        events = dict \
            ( Originate =
                ( Event
                    ( Response  = ('Success',)
                    , Message   = ('Originate successfully queued',)
                    )
                , Event
                    ( Event            = ('Newchannel',)
                    , Privilege        = ('call,all',)
                    , Channel          = ('lcr/557',)
                    , ChannelState     = ('1',)
                    , ChannelStateDesc = ('Rsrvd',)
                    , CallerIDNum      = ('',)
                    , CallerIDName     = ('',)
                    , AccountCode      = ('',)
                    , Exten            = ('',)
                    , Context          = ('',)
                    , Uniqueid         = ('1332366541.558',)
                    )
                , Event
                    ( Event            = ('NewAccountCode',)
                    , Privilege        = ('call,all',)
                    , Channel          = ('lcr/557',)
                    , Uniqueid         = ('1332366541.558',)
                    , AccountCode      = ('4019946397',)
                    , OldAccountCode   = ('',)
                    )
                , Event
                    ({ 'Event'           : ('NewCallerid',)
                     , 'Privilege'       : ('call,all',)
                     , 'Channel'         : ('lcr/557',)
                     , 'CallerIDNum'     : ('',)
                     , 'CallerIDName'    : ('',)
                     , 'Uniqueid'        : ('1332366541.558',)
                     , 'CID-CallingPres' :
                        ('0 (Presentation Allowed, Not Screened)',)
                    })
                , Event
                    ( Event            = ('Newchannel',)
                    , Privilege        = ('call,all',)
                    , Channel          = ('lcr/558',)
                    , ChannelState     = ('1',)
                    , ChannelStateDesc = ('Rsrvd',)
                    , CallerIDNum      = ('',)
                    , CallerIDName     = ('',)
                    , AccountCode      = ('',)
                    , Exten            = ('',)
                    , Context          = ('',)
                    , Uniqueid         = ('1332366541.559',)
                    )
                , Event
                    ( Event            = ('Newstate',)
                    , Privilege        = ('call,all',)
                    , Channel          = ('lcr/558',)
                    , ChannelState     = ('4',)
                    , ChannelStateDesc = ('Ring',)
                    , CallerIDNum      = ('0000000000',)
                    , CallerIDName     = ('',)
                    , Uniqueid         = ('1332366541.559',)
                    )
                , Event
                    ( Event            = ('Newstate',)
                    , Privilege        = ('call,all',)
                    , Channel          = ('lcr/558',)
                    , ChannelState     = ('7',)
                    , ChannelStateDesc = ('Busy',)
                    , CallerIDNum      = ('0000000000',)
                    , CallerIDName     = ('',)
                    , Uniqueid         = ('1332366541.559',)
                    )
                , Event
                    ({ 'Event'         : ('Hangup',)
                     , 'Privilege'     : ('call,all',)
                     , 'Channel'       : ('lcr/558',)
                     , 'Uniqueid'      : ('1332366541.559',)
                     , 'CallerIDNum'   : ('0000000000',)
                     , 'CallerIDName'  : ('<unknown>',)
                     , 'Cause'         : ('16',)
                     , 'Cause-txt'     : ('Normal Clearing',)
                    })
                , Event
                    ({ 'Event'         : ('Hangup',)
                     , 'Privilege'     : ('call,all',)
                     , 'Channel'       : ('lcr/557',)
                     , 'Uniqueid'      : ('1332366541.558',)
                     , 'CallerIDNum'   : ('<unknown>',)
                     , 'CallerIDName'  : ('<unknown>',)
                     , 'Cause'         : ('17',)
                     , 'Cause-txt'     : ('User busy',)
                    })
                , Event
                    ( Event            = ('OriginateResponse',)
                    , Privilege        = ('call,all',)
                    , Response         = ('Failure',)
                    , Channel          = ('LCR/Ext1/0000000000',)
                    , Context          = ('linecheck',)
                    , Exten            = ('1',)
                    , Reason           = ('1',)
                    , Uniqueid         = ('<null>',)
                    , CallerIDNum      = ('<unknown>',)
                    , CallerIDName     = ('<unknown>',)
                    )
                )
            )
        self.run_manager(events)
        r = self.manager.originate \
            ('LCR/Ext1/0000000000', '1'
            , context   = 'linecheck'
            , priority  = '1'
            , account   = '4019946397'
            , variables = {'CALL_DELAY' : '1', 'SOUND' : 'abandon-all-hope'}
            )
        self.compare_result(r, events['Originate'][0])
        for k in events['Originate'][1:]:
            n = self.queue.get()
            self.compare_result(self.events[n], events['Originate'][n+1])

    def test_misc_events(self):
        d = dict
        # Events from SF bug 3470641 
        # http://sourceforge.net/tracker/
        # ?func=detail&aid=3470641&group_id=76162&atid=546272
        # But we fail to reproduce the bug.
        events = dict \
            ( Login =
                ( self.default_events['Login'][0]
                , Event
                    ({ 'AppData'    : '0?begin2'
                     , 'Extension'  : 'zap2dahdi'
                     , 'Uniqueid'   : '1325950970.698'
                     , 'Priority'   : '9'
                     , 'Application': 'GotoIf'
                     , 'Context'    : 'macro-dial-one'
                     , 'Privilege'  : 'dialplan,all'
                     , 'Event'      : 'Newexten'
                     , 'Channel'    : 'Local/102@from-queue-a8ca;2'
                    })
                , Event
                    ({ 'Value'     : '2'
                     , 'Variable'  : 'MACRO_DEPTH'
                     , 'Uniqueid'  : '1325950970.698'
                     , 'Privilege' : 'dialplan,all'
                     , 'Event'     : 'VarSet'
                     , 'Channel'   : 'Local/102@from-queue-a8ca;2'
                    })
                , Event
                    ({'Privilege': 'dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 9\r\n'
                      'Application: GotoIf\r\n'
                      'AppData: 0?begin2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 10\r\n'
                      'Application: Set\r\n'
                      'AppData: THISDIAL=SIP/102\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: THISDIAL\r\n'
                      'Value: SIP/102\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 11\r\n'
                      'Application: Return\r\n'
                      'AppData: \r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: GOSUB_RETVAL\r\n'
                      'Value: \r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: dstring\r\n'
                      'Priority: 9\r\n'
                      'Application: Set\r\n'
                      'AppData: DSTRING=SIP/102&\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: DSTRING\r\n'
                      'Value: SIP/102&\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: dstring\r\n'
                      'Priority: 10\r\n'
                      'Application: Set\r\n'
                      'AppData: ITER=2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 6\r\n'
                      'Application: ExecIf\r\n'
                      'AppData: 0?Set(THISPART2=DAHDI/101)\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: ITER\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/102@from-queue-a8ca;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.698\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 7\r\n'
                      'Application: Set\r\n'
                      'AppData: NEWDIAL=SIP/101&\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: NEWDIAL\r\n'
                      'Value: SIP/101&\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 8\r\n'
                      'Application: Set\r\n'
                      'AppData: ITER2=2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: ITER2\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 9\r\n'
                      'Application: GotoIf\r\n'
                      'AppData: 0?begin2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: MACRO_DEPTH\r\n'
                      'Value: 2\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: Newexten\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Context: macro-dial-one\r\n'
                      'Extension: zap2dahdi\r\n'
                      'Priority: 10\r\n'
                      'Application: Set\r\n'
                      'AppData: THISDIAL=SIP/101\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2\r\n'
                      'Variable: THISDIAL\r\n'
                      'Value: SIP/101\r\n'
                      'Uniqueid: 1325950970.696\r\n'
                      '\r\n'
                      'Event: VarSet\r\n'
                      'Privilege: dialplan,all\r\n'
                      'Channel: Local/101@from-queue-4406;2'
                    , 'Variable': 'MACRO_DEPTH'
                    , 'Event': 'VarSet'
                    , 'Value': '2'
                    , 'Uniqueid': '1325950970.696'
                   })
                )
            )
        self.run_manager(events)
        r = self.manager.login('account', 'geheim')
        self.compare_result(r, events['Login'][0])
        evnames = []
        for s in events['Login'][3]['Privilege'].split('\r\n'):
            if s.startswith('Event:'):
                evnames.append(s.split(':')[1].strip())
        for k in xrange(30):
            n = self.queue.get()
            e = self.events[n]
            if n < 2:
                self.compare_result(e, events['Login'][n+1])
            elif n == 2:
                self.assertEqual(e['Event'], 'VarSet')
            else:
                self.assertEqual(e['Event'], evnames[n-3])
        self.assertEqual(len(self.events), 30)

    def test_agent_event(self):
        d = dict
        # Events from SF bug 3470641 
        # http://sourceforge.net/tracker/
        # ?func=detail&aid=3470641&group_id=76162&atid=546272
        # But we fail to reproduce the bug.
        events = dict \
            ( Login =
                ( self.default_events['Login'][0]
                , Event
                    ( Event              = ('AgentCalled',)
                    , Privilege          = ('agent,all',)
                    , Queue              = ('test',)
                    , AgentCalled        = ('SIP/s394000',)
                    , AgentName          = ('910567',)
                    , ChannelCalling     = ('SIP/multifon-00000006',)
                    , DestinationChannel = ('SIP/s394000-00000007',)
                    , CallerIDNum        = ('394000',)
                    , CallerIDName       = ('Agent',)
                    , Context            = ('from-multifon',)
                    , Extension          = ('7930456789',)
                    , Priority           = ('3',)
                    , Uniqueid           = ('1302010429.6',)
                    , Variable           = ('data1=456789', 'data2=test')
                    )
                )
            )
        self.run_manager(events)
        r = self.manager.login('account', 'geheim')
        self.compare_result(r, events['Login'][0])
        for k in events['Login'][1:]:
            n = self.queue.get()
            self.compare_result(self.events[n], events['Login'][n+1])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest (unittest.makeSuite (Test_Manager))
    return suite

if __name__ == '__main__':
    unittest.main()

