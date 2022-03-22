import socket
import threading
import time
from .stats import Stats

class Tello:
    def __init__(self):
        self.local_ip = ''
        self.local_port = 8889
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for sending cmd
        self.socket.bind((self.local_ip, self.local_port))

        self.local_state_port = 8890
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving status frames from tello
        self.state_socket.bind((self.local_ip, self.local_state_port))

        # thread for receiving cmd ack
        self.receive_thread = threading.Thread(target=self._cmd_ack_receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # thread for receiving status
        self.status_receive_thread = threading.Thread(target=self._status_receive_thread)
        self.status_receive_thread.daemon = True
        self.status_receive_thread.start()
        self.status=dict()

        self.tello_ip = '192.168.10.1'
        self.tello_port = 8889
        self.tello_adderss = (self.tello_ip, self.tello_port)
        self.log = []


    def send_command(self, command, timeout=10.0):
        """
        Send a command to the ip address. Will be blocked until
        the last command receives an 'OK'.
        If the command fails (either b/c time out or error),
        will try to resend the command
        :param command: (str) the command to send
        :param ip: (str) the ip of Tello
        :return: The latest command response
        """
        self.log.append(Stats(command, len(self.log)))

        self.socket.sendto(command.encode('utf-8'), self.tello_adderss)
        print('sending command: %s to %s' % (command, self.tello_ip))


        start = time.time()
        while not self.log[-1].got_response():
            now = time.time()
            diff = now - start
            if diff > timeout:
                print('Response timeout exceeded... command %s' % command)
                # TODO: is timeout considered failure or next command still get executed
                # now, next one got executed
                return
        print('Done!!! sent command: %s to %s' % (command, self.tello_ip))

    def _cmd_ack_receive_thread(self):
        """Listen to responses from the Tello.

        Runs as a thread, sets self.response to whatever the Tello last returned.

        """
        while True:
            try:
                self.response, ip = self.socket.recvfrom(1024)
                print('from %s: %s' % (ip, self.response))

                self.log[-1].add_response(self.response)
            except socket.error as exc:
                print("Caught exception socket.error : %s" % exc)

    def _status_receive_thread(self):
        while True:
            r, ip = self.state_socket.recvfrom(1024)
            r = ((r.decode('utf-8')).strip()).rstrip(";")
            tmp = r.split(';')
            status = dict(s.split(':') for s in tmp)
            for k in status: self.status[k]=float(status[k])
            #print(str(self.status))
            time.sleep(0.05)

    def close(self):
        # for ip in self.tello_ip_list:
        #     self.socket.sendto('land'.encode('utf-8'), (ip, 8889))
        self.socket.close()
        self.state_socket.close()

    def get_log(self):
        return self.log

