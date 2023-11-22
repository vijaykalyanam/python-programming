import paramiko

from data_class import NetworkInfo
from transport_handler import TransportHandler

SERVER = 0
CLIENT = 1

class RemoteClass:
    hostname : str = None
    username: str = None
    password: str = None

    network_info: NetworkInfo = NetworkInfo

    transport_list : TransportHandler = []

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

            self.GetNetworkInfo()
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
                    #print(fresult.decode())
                    raise Exception(f"{cmd} Result:{fresult.decode()}")
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

    def GetIPFromName(self, if_name: str):
        cmd = f"ip addr show dev {if_name}"
        cmd = cmd + " | grep inet | head -n 1 | awk '{print $2}' | cut -d '/' -f 1"
        return self.Get(cmd)

    def GetIPFromIndex(self, pf_index : int):
        #print(self.network_info)
        pf_name=self.network_info.pf_list[int(pf_index)]

        cmd=f"ip addr show dev {pf_name}"
        cmd=cmd+" | grep inet | head -n 1 | awk '{print $2}' | cut -d '/' -f 1"

        return self.Get(cmd)

    def GetRdmaDev(self, l2_dev: str):
        cmd=f"rdma link | grep {l2_dev}"
        cmd=cmd+" | awk '{print $2}' | cut -d '/' -f 1"
        return self.Get(cmd)

    def GetInterfaceFromIndex(self, pf_index: int):
        return self.network_info.pf_list[int(pf_index)]

    def GetNetworkInfo(self, nic_type : str = None):
        pf_list = []
        pf_pci_list = []
        vf_list = []
        vf_pci_list = []

        if nic_type == None:
            nic_type = "thor2"


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

        self.network_info = NetworkInfo(nic_type, pf_list, pf_pci_list)
        print(f"INIT: {self.network_info}")

    def GenerateIPerfTestPort(self, perf_test: str, pf_index: int = 0):
        return 23000+500*pf_index

    '''Flexible : provide either pf index or PF name'''
    def GenerateIPerfTestCommands(
            self, test_mode: int = 0, test_pf: str = None, pf_index: int = 0,
            perf_test: str = None, test_port: int = 0,
            test_instances: int = 1, test_duration: int = 120,
            cmn_opts: str = None, server_ip: str = None, **kwargs
            ):

        cmds_list = []

        if test_pf == None:
            l2_dev=self.GetInterfaceFromIndex(pf_index)
        else:
            l2_dev=test_pf

        #print(f"INTERFACES:: MODE {test_mode} {l2_dev} <-> {roce_dev}")
        #print(f"Preparing commands: {test_mode} {test_pf} {pf_index} {perf_test} {test_port} {server_ip}")

        port = self.GenerateIPerfTestPort ( perf_test, pf_index )
        cmd = f"{perf_test}"
        if test_mode == SERVER:
            cmd = cmd + " -s "
        else:
            cmd = cmd + f" -c {server_ip} "

        cmd = f"{cmd} -p {port} -P {test_instances} -t {test_duration}"

        print(f"MODE {test_mode} {cmd}")
        cmds_list.append(cmd)

        return cmds_list

    def GeneratePerfTestPort(self, perf_test: str, instance: int = 0, pf_index: int = 0):

        if perf_test == "ib_write_bw":
            test_port = 11000 + pf_index * 5000 + instance
        elif perf_test == "ib_read_bw":
            test_port = 21000 + pf_index * 5000 + instance
        if perf_test == "ib_send_bw":
            test_port = 31000 + pf_index * 5000 + instance
        elif perf_test == "ib_atomic_bw":
            test_port = 41000 + pf_index * 5000 + instance

        return test_port

    '''Flexible : provide either pf index or PF name'''
    def GeneratePerfTestCommands(
            self, test_mode: int = 0, test_pf: str = None, pf_index: int = 0,
            perf_test: str = None, test_port: int = 0,
            num_qps: int = 0, test_instances: int = 1, test_duration : int = 120,
            cmn_opts: str = None, server_ip: str = None, **kwargs
            ):

        cmds_list = []

        if test_pf == None:
            l2_dev=self.GetInterfaceFromIndex(pf_index)
        else:
            l2_dev=test_pf
        roce_dev = self.GetRdmaDev(l2_dev)

        #print(f"INTERFACES:: MODE {test_mode} {l2_dev} <-> {roce_dev}")
        #print(f"Preparing commands: {test_mode} {test_pf} {pf_index} {perf_test} {test_port} {server_ip}")
        for each_instance in range(0, test_instances):
            port=self.GeneratePerfTestPort(perf_test, each_instance, pf_index)
            cmd=f"{perf_test} -d {roce_dev} -x 3 -q {num_qps} -p {port} -D {test_duration}"
            if cmn_opts != None:
                cmd=cmd+cmn_opts
            if test_mode == CLIENT:
                cmd=cmd+f" {server_ip}"
            print(cmd)
            cmds_list.append(cmd)

        return cmds_list

    def Run(self, cmd):
        handler=TransportHandler(self.transport, cmd)
        self.transport_list.append(handler)
        handler.run()

    def GetHandler(self, cmd):
        print(f"XXXXXXXYYYYYZZZZZ:{cmd}")
        handler=TransportHandler(self.transport, cmd)
        self.handler=handler
        handler.run()
        return self.handler

    def Poll(self):
        return self.handler.poll()
