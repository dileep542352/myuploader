import socket
import threading
import sys
import argparse
import queue
import requests
import time
import random
import ipaddress

ot = ''
O = '\033[1;36m'
T = ot + '\033[32m'
B = ot + '\033[33;3m'
TE = ot + '\033[37m'
E = ot + '\033[31m'

def convert_ip_ranges_to_list(ip_ranges):
    ip_list = []
    for ip_range in ip_ranges:
        if '/' in ip_range:
            network = ipaddress.ip_network(ip_range, strict=False)
            for ip in network:
                ip_list.append(str(ip))
        else:
            ip_list.append(ip_range)
    return ip_list

class Scanner:
    def __init__(self):
        self.queue = queue.Queue()
        self.request = requests.get
        self.thread = threading.Thread
        self.total = 1
        self.progress = 1
        self.lock = threading.Lock()

    def setupqueue(self):
        while True:
            ip = str(self.queue.get())
            with self.lock:
                sys.stdout.write(f'scanning...{ip} ==> progressing....  ({self.progress}/{self.total})\r')
                sys.stdout.flush()
            self.Sendrequest(ip)
            self.queue.task_done()

    def Sendrequest(self, ip):
        url = (f'https://{ip}' if self.port == 443 else f'http://{ip}:{self.port}')
        try:
            headers = {'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) RockMelt/0.9.58.494 Chrome/11.0.696.71 Safari/534.24',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.54 Safari/535.2',
                'Opera/9.80 (X11/Linux; Opera Mobi/23.348; U; en) Presto/2.5.25 Version/10.54',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
                'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.6 (KHTML, like Gecko) Chrome/16.0.897.0 Safari/535.6',
                'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20121202 Firefox/17.0 Iceweasel/17.0.1'
            ])}
            if self.proxy:
                proxyhost, port = self.proxy.split(':')
                proxy = {'http': f'http://{proxyhost}:{port}', 'https': f'http://{proxyhost}:{port}'}
                req = self.request(url, proxies=proxy, headers=headers, timeout=7, allow_redirects=False)
            else:
                req = self.request(url, headers=headers, timeout=7, allow_redirects=False)

            status = req.status_code
            server = req.headers.get('server', 'N/A')
            x_ray = req.headers.get('x-ray', 'N/A')

            response = f'\n{O} [+] {T}{ip}\n{status}\n{server}\nPS-RAY: {x_ray}{TE}\r\n'

            if 'cloudflare' in server.lower() or 'cloudfront' in server.lower():
                if status in [200, 301, 403]:
                    with open('cloudflare_cloudfront_results.txt', 'a') as file:
                        file.write(response)
            else:
                if status == 200:
                    with open('successful_results.txt', 'a') as file:
                        file.write(response)

            with self.lock:
                sys.stdout.write(response)
                sys.stdout.flush()

        except Exception as e:
            with self.lock:
                status = 'N/A'
                server = 'N/A'
                x_ray = 'N/A'
                response = f'\n [-] {E}{ip}\n{status}\n{server}\nPS-RAY: {x_ray}\nError: {str(e)}{TE}\r\n'
                sys.stdout.write(response)
                sys.stdout.flush()

                if self.output:
                    with open(self.output, 'a') as file:
                        file.write(response)

        with self.lock:
            self.progress += 1

def main(user_input):
    sys.stdout.write(f'{B}Converting ip_ranges to single IPs ...\n')
    sys.stdout.flush()

    ip_addresses = convert_ip_ranges_to_list(user_input)

    for ip in ip_addresses:
        pqafpna.queue.put(ip)
        pqafpna.total += 1

    sys.stdout.write(f'{B}Done 💀 Scanning starts {TE}\n')
    sys.stdout.flush()

    threadrun()

def threadrun():
    for _ in range(pqafpna.threads):
        thread = pqafpna.thread(target=pqafpna.setupqueue)
        thread.start()

    pqafpna.queue.join()

def read_ip_file(file_path):
    try:
        with open(file_path, 'r') as file:
            ip_addresses = [line.strip() for line in file if line.strip()]
        return ip_addresses
    except FileNotFoundError:
        print(f"{E}Error: File not found.{TE}")
        sys.exit(1)

def parseargs():
    global pqafpna
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52)
    )
    parser.add_argument(
        "ip_input", metavar="IP_INPUT", nargs="?", help="Enter the IP range (/24) or specify a file with -s"
    )
    parser.add_argument(
        "-t", "--threads", help="num of threads", dest="threads", type=int, default=10
    )
    parser.add_argument(
        "-p", "--port", help="port to scan", dest="port", type=int, default=80
    )
    parser.add_argument(
        "-P",
        "--proxy",
        help="proxy ip:port ex: 12.34.56.6:80",
        dest="proxy",
        type=str,
    )
    parser.add_argument(
        "-o", "--output", help="save output in file", dest="output", type=str
    )
    parser.add_argument(
        "-s", "--file", help="read IP addresses from a file", dest="file", type=str
    )

    args = parser.parse_args()

    pqafpna = Scanner()
    pqafpna.threads = args.threads
    pqafpna.port = args.port
    pqafpna.proxy = args.proxy
    pqafpna.output = args.output

    if args.file:
        ip_addresses = read_ip_file(args.file)
    else:
        ip_addresses = [args.ip_input] if args.ip_input else []

    main(ip_addresses)

if __name__ == "__main__":
    parseargs()
