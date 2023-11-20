import paramiko

from data_class import NetworkInfo
from transport_handler import TransportHandler


class RemoteClass:
    hostname : str = None
    username: str = None
    password: str = None

    network_info: NetworkInfo = None

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

        try:
            #print(f"Connection.... {self.hostname} {self.username} {self.password}")
            transport = paramiko.Transport(self.hostname, default_window_size=65536)
            transport.connect(username=self.username, password=self.password)
            self.transport=transport

            self.network_info = self.GetNetworkInfo()
            print(self.network_info)

        except:
            raise Exception(f"Failed to ssh connect:{self.hostname}")

    def ShellCmd(self, cmd):

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
                    #print(fresult.decode())
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
                #print(f"{cmd}:")
                #print(f"{sresult.decode()}")
                #print(f"{fresult.decode()}")
                break;

        session.close()

        if fresult:
            return ret, fresult

        if sresult:
            return ret, sresult

    def Get(self, cmd) -> str:

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
                    raise Exception("{cmd} {}")
                else:
                    while session.recv_ready():
                        result=session.recv(buffSize)
                        sresult = sresult+result
                    exit_loop=True

            if session.recv_ready():
                 result = session.recv(buffSize)
                 sresult = sresult+result
             #    print(sresult)

            if exit_loop:
                #print(f"{cmd}:")
                #print(f"{sresult.decode()}")
                #print(f"{fresult.decode()}")
                break;

        session.close()

        print(f"{cmd}")
        result = sresult.decode()
        print(result)
        return result.strip()

    def GetInterfaceIP(self, if_name: str):
        print("")

    def GetNetworkInfo(self, nic_type : str = None):

        pf_list = []
        pf_pci_list = []
        vf_list = []
        vf_pci_list = []

        if nic_type == None:
            nic_type = "thor2"

        network_info = NetworkInfo(nic_type)
        print(network_info)

        if nic_type == "whp":
            PF_IDENTIFIER="BCM57414"
            VF_IDENTIFIER=""
        else:
            #PF_IDENTIFIER="Broadcom Inc. and subsidiaries Device 1760"
            PF_IDENTIFIER="Broadcom Inc."
            VF_IDENTIFIER="Broadcom Inc. and subsidiaries Device 1819"

        cmd=f'lshw -businfo -class network | grep "{PF_IDENTIFIER}" -c'
        if int(self.Get(cmd)) == 0:
            raise Exception("There were no devices....")

        cmd=f'lshw -businfo -class network | grep "{PF_IDENTIFIER}"'
        lshw_info=self.Get(cmd)

        for each_line in lshw_info.split('\n'):
            #print(f"==> :{each_line}")
            pci=each_line.split()[0]
            if_name=each_line.split()[1]
            #print(f"X::{pci.split('@')[1]} {if_name}")

            pf_pci_list.append(pci.split('@')[1])
            pf_list.append(if_name)

        print(pf_list)
        print(pf_pci_list)

    def Run(self, cmd):

        handler=TransportHandler(self.transport, cmd)
        self.handler=handler
        handler.run()

    def Poll(self):
        return self.handler.poll()
