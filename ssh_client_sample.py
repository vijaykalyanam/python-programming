import paramiko

hostname = "10.10.10.10"
username = "root"
password = "root"

# initialize the SSH client
client = paramiko.SSHClient()
# add to known hosts
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(hostname=hostname, username=username, password=password)
except:
    print("[!] Cannot connect to the SSH Server")
    exit()

# read the BASH script content from the file
# execute the BASH script
#remote_cmd="lscpu"
remote_cmd="ping -c 10 10.123.66.111"
stdin, stdout, stderr = client.exec_command(remote_cmd)
# read the standard output and print it
print(stdout.read().decode())
# print errors if there are any
err = stderr.read().decode()
if err:
    print(err)
# close the connection
client.close()
