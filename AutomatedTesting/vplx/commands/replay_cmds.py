import argparse
from log import Log
from replay import Replay,LogDB




class ReplayCommands():
    def __init__(self,parser):
        self.parser = parser

    def setup_commands(self, subp):
        # replay function related parameter settings
        parser_replay = subp.add_parser(
            'replay',
            aliases=['re'],
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='transactionid',
            metavar='',
            help='transaction id')

        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='date')

        parser_replay.add_argument(
            '-l',
            '--lite',
            dest='lite',
            action='store_true',
            default=False,
            help='lite mode')

        parser_replay.set_defaults(func=self.replay)


    def replay(self, args):
        Log.log_switch = False
        Replay.switch = True
        if args.lite:
            Replay.mode = 'LITE'
            print('* MODE : LITE *')
            if args.transactionid and args.date:
                print('Please specify only one type of data for replay')
                return
            elif args.transactionid:
                Replay().replay_execute(self.parser,transaction_id=args.transactionid)
            elif args.date:
                Replay().replay_execute(self.parser,start_time=args.date[0],end_time=args.date[1])
            else:
                Replay().replay_execute(self.parser)
        else:
            print('* MODE : REPLAY *')
            if args.transactionid and args.date:
                print('Please specify only one type of data for replay')
                return
            elif args.transactionid:
                Replay().replay_execute(self.parser,transaction_id=args.transactionid)
            elif args.date:
                Replay().replay_execute(self.parser,start_time=args.date[0],end_time=args.date[1])
            else:
                Replay().replay_execute(self.parser)
