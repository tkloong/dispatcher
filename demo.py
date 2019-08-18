import argparse
import time

parser = argparse.ArgumentParser(description='Dispatcher')
parser.add_argument('-n',
                    type=int,
                    metavar='interval of time (sec) for suspension',
                    required=True,
                    help='interval of time (sec) for suspension')
args = parser.parse_args()

time.sleep(args.n)
print('Hello world!')
