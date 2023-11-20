from remote_class import RemoteClass


class ConnectionClass:

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

iperf=ConnectionClass("10.123.66.111", "root", "password",
                     "10.123.66.222", "root", "password")
