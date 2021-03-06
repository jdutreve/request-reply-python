#!/usr/bin/env python

import time
import sys
from datetime import datetime
from threading import Thread

import zmq

from rpc_agent_thread import FreelanceClient

ZMQ_AGAIN = zmq.Again


# 471K  req/s with 1 client x 600 000 requests GO
# 198K  req/s with 1 client x 600 000 requests Python
# 194K  req/s with 1 client x 600 000 requests PyPy
# 184K  req/s with 1 client x 600 000 requests Jzmq
# 174K  req/s with 1 client x 600 000 requests Jeromq
#
# 213K  req/s with 6 clients x 600 000 requests GO
# 107K  req/s with 6 clients x 600 000 requests Python
# 85K   req/s with 6 clients x 600 000 requests PyPy
#
# QOS
#   remove @TODO
#   more fair load balancing
#   fixer l'arrêt d'un seul server
# PING/PONG client
#           quid des PING queued/delayed (behind a lot of requests)?
#           client should squeeze too ancient returned PONGs
#               sending a lot PINGs to an expired server, will it reply a lot of (thousands) PONGS?
#           use tickless (finer grained heartbeat timeout)
#           different PING timeout per worker (depending on usage; ex: every 10ms or every 30s)
#  correct shutdown : LINGER sockopt, use disconnect?

REQUEST_NUMBER = 600_000

port = sys.argv[1] if len(sys.argv) > 1 else "5555"


def p(msg):
    pass
    # print('%s   %s' % (datetime.now().strftime('%M:%S:%f')[:-3], msg))


def send_all_requests():
    for request_nb in range(1, REQUEST_NUMBER+1):
        client.request(request_nb, "REQ%d" % request_nb)
    print("SEND REQUESTS FINISHED")


def read_all_replies():

    send_all_requests()

    reply_nb = 0
    while 1:
        try:
            while 1:
                request_id, reply = client.receive()
                reply_nb += 1
                # p("%d %s %d +++++++++++++++++++++++++++++++++++" % (request_id, reply, reply_nb))
                if reply_nb == REQUEST_NUMBER:
                    print("**************************** READ REPLIES FINISHED ****************************")
                    return
        except IndexError:
            # print("NOTHING TO RECEIVE %d" % reply_nb)
            time.sleep(0.01)  # should not be MUCH smaller (else worst performance)


def finish(start):
    duration = time.time() - start
    print("duration %s" % duration)
    print("Rate: %d req/s ======================================================================" % (REQUEST_NUMBER / duration))
    # import statistics
    # print("REPLY NB = %d" % rpc_agent.agent.reply_nb)
    # print("FAILED NB = %d" % rpc_agent.agent.failed_nb)
    # print("LATENCY p50 = %fms" % (statistics.median(rpc_agent.agent.latencies)*1000))
    # print("LATENCY p90 = %fms" % ([round(q, 1000) for q in statistics.quantiles(rpc_agent.agent.latencies, n=10)][-1]*1000))
    # with open('latencies.csv', 'w') as f:
    #     for i in rpc_agent.agent.latencies:
    #         f.write("%s\n" % str(i))
    # print("RETRY NB = %d" % rpc_agent.retry_nb)


def init_client(client):
    # client.connect("tcp://192.168.0.22:5557")
    # client.connect("tcp://192.168.0.22:5558")
    # client.connect("tcp://192.168.0.22:5556")
    # client.connect("tcp://192.168.0.22:5555")
    client.connect(f"tcp://192.168.0.22:{port}")


client = FreelanceClient()
init_client(client)


def main():
    # import yappi
    # yappi.set_clock_type("WALL")
    # yappi.start()

    start = time.time()

    Thread(target=client.agent.read_replies_send_requests).start()
    read_all_replies()

    finish(start)

    # yappi.get_func_stats().print_all(columns={0: ("name", 100), 1: ("ncall", 10), 2: ("tsub", 8), 3: ("ttot", 8), 4: ("tavg", 8)})
    # yappi.stop()

main()
