import atexit
import time
from multiprocessing import Process
from multiprocessing import Pool

from remote_class import RemoteClass

SERVER = 0
CLIENT = 1

class ConnectionClass:

    process_list = []

    def __init__(self,
                 sut : str, username1: str, password1 :str,
                 put: str, username2: str, password2 : str):
        self.sut=sut
        self.username1=username1
        self.password1=password1
        self.put=put
        self.username2=username2
        self.password2=password2

        try:
            self.Sut=RemoteClass(hostname=self.sut,username=self.username1,password=self.password1)
            self.Put=RemoteClass(hostname=self.put,username=self.username2,password=self.password2)

        except:
            raise Exception("Could not establish connection")

    '''IF THIS FUNCTION IS RUNNING,,,, ie; it is running as different process'''
    def __ProcessExecutor__(self, server_cmds : [], client_cmds : []):
        print("__ProcessExecutor__")
        print(server_cmds)
        print(client_cmds)

        #Server = self.Sut
        #Client = self.Put

        Server= RemoteClass( hostname=self.sut, username=self.username1, password=self.password1 )
        Client = RemoteClass( hostname=self.put, username=self.username2, password=self.password2 )

        server_handlers = []
        client_handlers = []

        '''Run server commands'''
        num_lists=len(server_cmds)
        print(f"Server command num lists:{num_lists}")

        for index, each_list in enumerate(server_cmds):
            for each_cmd in each_list:
                print(f"RUNNING SERVER COMMAND:{each_cmd}")
                #time.sleep(20)
                handle=Server.GetHandler(each_cmd)
                server_handlers.append(handle)

        for each_handle in server_handlers:
            if each_handle.error:
                print("Failed to run command in Server:")
                print(f"command: {each_handle.cmd}")
                print(f"INFO:{each_handle.sresult}")
                print(f"ERROR: {each_handle.fresult}")
                raise Exception("Failed to run server commands....")

        for index, each_list in enumerate(client_cmds):
            for each_cmd in each_list:
                print(f"RUNNING CLIENT COMMAND:{each_cmd}")
                #time.sleep(20)
                handle=Client.GetHandler(each_cmd)
                client_handlers.append(handle)

        num_servers=len(server_cmds)
        num_clients=len(client_cmds)
        server_logouts=0
        client_logouts=0
        while 1:
            for each_client in client_handlers:
                '''EXIT Status Ready'''
                if each_client.poll() and each_client.active:
                    print(f"{each_client.cmd} return code {each_client.ret}")
                    #print(f"{each_client.sresult.decode()}")
                    #print(f"{each_client.fresult.decode()}")

                    each_client.active=False
                    client_logouts=client_logouts+1
                    print(f"{each_client.active} {client_logouts}")

            for each_server in server_handlers:
                '''EXIT Status Ready'''
                if each_server.poll() and each_server.active:
                    print( f"SERVER::{each_server.cmd} return code {each_server.ret}" )
                    #print( f"{each_server.sresult.decode()}" )
                    #print( f"{each_server.fresult.decode()}" )

                    each_server.active = False
                    server_logouts = server_logouts + 1
                    print(f"{each_client.active} {client_logouts}")

            if (len(server_handlers) == server_logouts) and (len(client_handlers) == client_logouts):
                print("Finished all the commands.....")
                exit(0)

            time.sleep(0.5)

    def ProcessExecutor(self, server_cmds : [], client_cmds : [], process_name: str = None):
        server=self.Sut
        client=self.Put

        if len(server_cmds) != len(client_cmds):
            raise Exception("Mismatch command list")

        process=Process(target=self.__ProcessExecutor__, args=(server_cmds, client_cmds))
        if process_name != None:
            process.name=process_name

        self.process_list.append(process)
        try:
            process.start()
        except:
            raise Exception(f"Failed to run process:{process.name}")

    def ProcessPoller(self):
        print("Polling the processes...")

        while 1:
            for each_process in self.process_list:
                if each_process.is_alive():
                    print(f"{each_process.name} is alive")
                else:
                    print(f"{each_process.name} exited with {each_process.exitcode}")
                    self.process_list.remove(each_process)
            if len(self.process_list) == 0:
                print("All tests finished....")
                exit(0)

            time.sleep(10)

    def TestPerfTest(self,
                     perf_test : str = None, test_port : int = 0,
                     num_qps : int = 1, test_instances :int = 2,
                     test_duration : int = 0,
                     cmn_opts : str = None, **kwargs):

        server_cmds = []
        client_cmds = []

        if perf_test == None:
            perf_test = "ib_write_bw"

        cmd=f"pkill {perf_test}"
        self.Sut.ShellCmd(cmd)
        self.Put.ShellCmd(cmd)

        for index, each_pf in enumerate(self.Sut.network_info.pf_list):
            cmd = self.Sut.GeneratePerfTestCommands(test_mode=SERVER, test_pf=each_pf, pf_index=index,
                                                    perf_test=perf_test, test_port=test_port, num_qps=num_qps,
                                                    test_instances=test_instances, test_duration = test_duration,
                                                    cmn_opts=cmn_opts, **kwargs
                                                    )

            pf_ip_address=self.Sut.GetIPFromName(each_pf)
            server_cmds.append(cmd)

            cmd = self.Put.GeneratePerfTestCommands(test_mode=CLIENT, test_pf = None, pf_index=index,
                                                     perf_test=perf_test, test_port=test_port, num_qps=num_qps,
                                                     test_instances=test_instances, server_ip=pf_ip_address
                                                     )
            client_cmds.append(cmd)


        print("Server Commands:")
        print(server_cmds)
        print("Client Commands:")
        print(client_cmds)

        self.ProcessExecutor(server_cmds, client_cmds, process_name=perf_test)


    def TestPing(self):

        for index, each_pf in enumerate(self.Sut.network_info.pf_list):
            put_pf_ip=self.Put.GetIPFromIndex(index)
            cmd="ping -c 1 "+put_pf_ip
            print(cmd)
            result=self.Sut.Get(cmd)

            for each_line in result.splitlines():
                if "0% packet loss" in each_line:
                    print(f"Ping SUCCESS on {each_pf}")

            print(result)

    def TestRping(self, port:int, cmn_opts:str=None):

        cmd="pkill rping"
        self.Sut.ShellCmd(cmd)
        self.Put.ShellCmd(cmd)

        '''START Commands.....'''
        for each_pf in self.Sut.network_info.pf_list:
            scmd = "rping -s -S 65530 -C 1024"
            ccmd = "rping -c -S 65530 -C 1024"
            server_ip=self.Sut.GetIPFromName(each_pf)
            ccmd=ccmd+" -p "+str(port)+" "+server_ip
            print({scmd})
            print({ccmd})
            self.Sut.Run(scmd)
            self.Put.Run(ccmd)
            port=port+1

    def TestIPerf(self,
                     perf_test : str = "iperf", test_port : int = 0,
                     test_instances :int = 2, cmn_opts : str = None,
                    test_duration: int = 120, **kwargs):

        server_cmds = []
        client_cmds = []

        cmd=f"pkill iperf"
        self.Sut.ShellCmd(cmd)
        self.Put.ShellCmd(cmd)

        for index, each_pf in enumerate(self.Sut.network_info.pf_list):
            cmd = self.Sut.GenerateIPerfTestCommands(test_mode=SERVER, test_pf=each_pf, pf_index=index,
                                                     perf_test=perf_test, test_port=test_port,
                                                     test_instances=test_instances
                                                     )
            server_cmds.append(cmd)

            pf_ip_address = self.Sut.GetIPFromName( each_pf )
            cmd = self.Put.GenerateIPerfTestCommands(test_mode=CLIENT, test_pf = None, pf_index=index,
                                                     perf_test=perf_test, test_port=test_port,
                                                     test_instances=test_instances, server_ip=pf_ip_address
                                                     )
            client_cmds.append(cmd)


        print("Server Commands:")
        print(server_cmds)
        print("Client Commands:")
        print(client_cmds)

        self.ProcessExecutor(server_cmds, client_cmds, process_name=perf_test)


