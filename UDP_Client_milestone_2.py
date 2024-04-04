import socket
import hashlib
import time
# import matplotlib.pyplot as plt

entryID = "2021CS11211"
team = "aakubhai"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(0.1)
server_host = "vayu.iitd.ac.in"
server_port = 9802

send_reset_request = "SendSize\nReset\n\n"
client_socket.sendto(send_reset_request.encode(), (server_host, server_port))

response, server_address = client_socket.recvfrom(4096)
response_str = response.decode("utf-8")

data_size = 0

if response_str.startswith("Size: "):
    data_size = int(response_str.split(' ')[1])

size = int(data_size)
print(f"Size: {size}")

i = 0
check = [0]
while (i<size):
    i += min(1448, size - i)
    check.append(i)


def findOffset(s):
    i = 8
    num = ""
    while i < len(s):
        # print(s[i])
        if s[i] == '\n':
            return int(num)
        else:
            num += s[i]
        i += 1


# data_received = ""
max_chunk_size = 1448

offset = 0
data_hash = {}

burst_size = 5
requests = 0
offsets_received = set()

start_time = time.time()

sentx = []
senty = []

receivedx = []
receivedy = []

while offset<size:
    # print("burst size: ", burst_size," offset: ", offset, "len of hash received: ", len(data_hash))
    requests = 0
    while requests<burst_size:
        num_bytes = min(max_chunk_size, size - offset)
        data_request = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
        print("sending offset :", offset, "at t = ", time.time() - start_time)
        sentx.append(time.time() - start_time)
        senty.append(offset)
        client_socket.sendto(data_request.encode(), (server_host, server_port))
        # time.sleep(0.01)
        requests += 1
        offset += num_bytes
    # print("burst size requests sent")
    
    requests_received = 0

    count = 0

    while count<=burst_size:
        count += 1
        try:
            data_response, _ = client_socket.recvfrom(4096)
            # print("came") 
            time.sleep(0.01)
            if data_response.decode().startswith("Offset"):   #changed f"Offset: {offset}" to "Offset"
                split_lines = data_response.decode().split('\n\n')
                try:
                    third_line = split_lines[1]
                except:
                    print("dengindi")
                if third_line.startswith("Squished"):
                    pass   #break or pass confusion
                else:
                    data = split_lines[1]
                    offset_line = split_lines[0]
                    # offset_number_received = offset_line[8:-8]
                    off = findOffset(offset_line)
                    # print("offset_number_received :", offset_number_received)
                    # print("off :", off )
                    data_hash[off] = data
                    print("received offset :", off, "at t = ", time.time() - start_time)
                    receivedx.append(time.time() - start_time)
                    receivedy.append(off)
                    offsets_received.add(off)
                    requests_received += 1         
        except socket.timeout:   #this mean does it wait for 0.1sec for the server
            pass

    if requests_received >= burst_size:
        burst_size += 1
    else:
        burst_size = burst_size//2


print("burst completed")
print("len of data hash :", len(data_hash))
print("len of offsets received is :", len(offsets_received))


print()
print()

retry_counter = 0
retry_limit = 100

new_offset = 0
not_there = []
data_hash_sorted_keys = sorted(data_hash.keys())
# print("keys of data_hash :", data_hash_sorted_keys)
while new_offset < size:
    # print("new_offset :", new_offset)
    NumBytes = min(max_chunk_size, size - new_offset)
    if new_offset not in data_hash:
        not_there.append(new_offset)
    new_offset += NumBytes

# print("len of not there :", len(not_there))
# print("not there :", not_there)

i = 0
#week 1 code maintaining reliability
while i < len(not_there):
    # print("new_offset :", new_offset)
    new_offset = not_there[i]

    

    try:
        NumBytes = min(size - new_offset, max_chunk_size)
        data_request = "Offset: "+str(new_offset)+"\nNumBytes: "+str(NumBytes)+"\n\n"

        # if len(data_hash)%25==0:
            # print("len of hash :", len(data_hash)*1448, "received time = ", time.time() - start_time)
        
        client_socket.sendto(data_request.encode(), (server_host, server_port))
        data_response, _ = client_socket.recvfrom(4096)
        time.sleep(0.01)
        if data_response.decode().startswith(f"Offset: {new_offset}"):
            data = data_response.decode().split('\n\n')[1]
            data_hash[new_offset] = data
            offsets_received.add(new_offset)
            i += 1

    except socket.timeout:
        if retry_counter < retry_limit:
            count += 1
            retry_counter += 1
            # print("Timeout! Retrying...")
            # time.sleep(0.01)
            continue
        else:
            print("Timeout! Max retries exceeded. Exiting...")
            time.sleep(0.001)
            break

print("len of offsets is :", len(offsets_received))


data_received = ""
data_hash_sorted_keys = sorted(data_hash.keys())


# print("keys of data_hash :", data_hash_sorted_keys)
# print("time retrying is repeated :", count, " times ")
for ele in data_hash_sorted_keys:
    data_received += data_hash[ele]


# print("data received is \n:", data_received)

# print("repeat = ", repeat)

md5_hash = hashlib.md5(data_received.encode()).hexdigest()

submit_request = f"Submit: 123@aku\nMD5: "+str(md5_hash)+"\n\n"
client_socket.sendto(submit_request.encode(), (server_host, server_port))

# response, _ = client_socket.recvfrom(1024)
# response_str = response.decode("utf-8")
# print(response_str)

# client_socket.close()
while True:
    try:
        response, _ = client_socket.recvfrom(1024)
        response_str = response.decode("utf-8")
        if response_str.startswith("Result"):
            print(response_str)
            break
    except TimeoutError:
        client_socket.settimeout(1.0)

    time.sleep(0.01)
client_socket.close()