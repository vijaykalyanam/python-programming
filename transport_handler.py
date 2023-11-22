import time
import paramiko

class TransportHandler:
    cmd : str = None
    transport : paramiko.Transport = None
    sresult: bytes = bytes(0)
    fresult: bytes = bytes(0)
    ret: int = -1
    error: int = 0

    def __init__(self, transport: paramiko.Transport, cmd :str):

        self.cmd=cmd
        self.transport=transport

        try:
            session=self.transport.open_session()
            self.session = session

        except:
            raise Exception("Failed to Launch session")

    def poll(self):

        buffSize = 4096

        session=self.session
        if session.exit_status_ready():
            ret = session.recv_exit_status()
            if ret != 0:
                self.fresult=session.recv_stderr(buffSize)
            else:
                if session.recv_ready():
                    result = session.recv(buffSize)
                    self.sresult = self.sresult + result

            self.ret=ret
            return True

        if session.recv_ready():
            result = session.recv(buffSize)
            self.sresult = self.sresult + result

        '''Command is still running.....'''
        return False

    def wait(self):
        print("wait")

    def kill(self):
        print("kill")

    def close(self):
        print(f"close {self.cmd}")
        self.session.close()

    def run(self):
        self.session.exec_command(self.cmd)
        self.active=True

        buffSize = 4096
        session=self.session

        time.sleep(1)
        if session.exit_status_ready():
            ret = session.recv_exit_status()
            if ret != 0:
                self.fresult=session.recv_stderr(buffSize)
                print(self.fresult)
                self.error=1
                #raise Exception(f"{self.cmd} failed with {ret}")

