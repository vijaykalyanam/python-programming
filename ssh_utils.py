import logging
import time

import paramiko


def close_ssh_connection(ssh):
    # close the connection
    logging.info("Closing SSH Connection!")
    ssh.close()
    exit()


# def setup_test_env(ssh):
def remote_cmd(ssh, remote_cmd):
    logging.info("Remote Cmd: {}".format(remote_cmd))
    stdin, stdout, stderr = ssh.exec_command(remote_cmd)
    remote_cmd_result = stdout.read().decode()
    logging.info("Result: {}".format(remote_cmd_result))

    # logging.info errors if there are any
    err = stderr.read().decode()
    if err:
        logging.info(err)
    return remote_cmd_result, err


# def setup_test_env(ssh):
def invoke_shell_cmd(ssh, remote_cmd):
    logging.info("Remote shell Cmd: {}".format(remote_cmd))
    stdin, stdout, stderr = ssh.send(remote_cmd + "\n")
    remote_cmd_result = stdout.read().decode()
    logging.info("Result: {}".format(remote_cmd_result))

    # logging.info errors if there are any
    err = stderr.read().decode()
    if err:
        logging.info(err)
    return remote_cmd_result, err


class SshConnection:

    hostname : str = None
    username: str = None
    password: str = None

    def __init__(self, hostname : str = None, username: str = None, password : str = None,
                 **kwargs):

        if hostname == None:
            self.hostname = "localhost"
            self.username = "root"
            self.password = "password"
        else:
            self.hostname = hostname
            self.username = username
            self.password = password

        print(f"__INIT__.... {self.hostname} {self.username} {self.password}")

        try:
            print(f"Connection.... {self.hostname} {self.username} {self.password}")
            transport = paramiko.Transport(self.hostname, default_window_size=65536)
            transport.connect(username=self.username, password=self.password)
            self.transport=transport
        except:
            raise Exception(f"Failed to ssh connect:{self.hostname}")


    def Get(self, cmd):

        sresult : bytes = bytes(0)
        fresult : bytes = bytes(0)

        session=self.transport.open_session()
        session.exec_command(cmd)
        #time.sleep(1)
        buffSize=4096

        exit_loop = False
        while True:
            if session.exit_status_ready():
                ret=session.recv_exit_status()
                if ret != 0:
                    fresult=session.recv_stderr(buffSize)
                    print(fresult.decode())
                    exit_loop = 1
                else:
                    while session.recv_ready():
                        result=session.recv(buffSize)
                        sresult = sresult+result
               # print(sresult)
                    exit_loop = 1

            if session.recv_ready():
                 result = session.recv(buffSize)
                 sresult = sresult+result
             #    print(sresult)

            if exit_loop:
                print(f"{cmd}:")
                print(f"{sresult.decode()}")
                #print(f"{fresult}")
                break;

        session.close()



localhost=SshConnection(hostname="10.123.66.222",
                        username="root", password="password")
localhost.Get("lscpu")
localhost.Get("iperf -c 197.168.10.222 -i 1 -P 12 -t 10")
localhost.Get("ib_write_bw -d bnxt_re2 -x 3 -q 8000 -u 34 197.168.10.222 -D 20")
