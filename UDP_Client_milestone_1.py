import socket
import hashlib
import time
entryID = "2021CS11211"
team = "aakubhai"
# bucket_size = 10
token_rate = 1
# tokens = bucket_size
last_time = time.time()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(0.1)
server_host = "vayu.iitd.ac.in"
server_port = 9801

send_size_request = "SendSize\nReset\n\n"


client_socket.sendto(send_size_request.encode(), (server_host, server_port))


start_time = time.time()   #this is start tim
print("started time = ", time.time() - start_time)
response, server_address = client_socket.recvfrom(4096)

response_str = response.decode("utf-8")


data_size = 0



if response_str.startswith("Size: "):
    data_size = int(response.decode().split(' ')[1])


size = int(data_size)
print(f"Size: {size}")


data_received = ""
total_data_received = 0
max_chunk_size = 1448
penalty = 0
retry_limit = 10000
retry_counter = 0
Offset = 0
data_hash = {}

repeat = 0
while Offset < size:
    # if len(data_hash)%25==0:
    #     print("len of hash :", len(data_hash)*1448, "Offset time = ", time.time() - start_time)
    try:
        NumBytes = min(max_chunk_size, size - Offset)
        data_request = "Offset: "+str(Offset)+"\nNumBytes: "+str(NumBytes)+"\n\n"

        # if len(data_hash)%25==0:
        #     print("len of hash :", len(data_hash)*1448, "received time = ", time.time() - start_time)
        
        client_socket.sendto(data_request.encode(), (server_host, server_port))
        data_response, _ = client_socket.recvfrom(4096)
        time.sleep(0.01)
        if data_response.decode().startswith(f"Offset: {Offset}"):
            data = data_response.decode().split('\n\n')[1]
            if Offset in data_hash:
                repeat += 1
            data_hash[Offset] = data
            Offset += NumBytes
    except socket.timeout:
        if retry_counter < retry_limit:
            retry_counter += 1
            # print("Timeout! Retrying...")
            time.sleep(0.01)
            continue
        else:
            print("Timeout! Max retries exceeded. Exiting...")
            time.sleep(0.01)
            break
    

data_hash_sorted_keys = sorted(data_hash.keys())

for ele in data_hash_sorted_keys:
    data_received += data_hash[ele]

# print("repeat = ", repeat)

md5_hash = hashlib.md5(data_received.encode()).hexdigest()

submit_request = f"Submit: 123@aku\nMD5: "+str(md5_hash)+"\n\n"
client_socket.sendto(submit_request.encode(), (server_host, server_port))

response, _ = client_socket.recvfrom(1024)
response_str = response.decode("utf-8")
print(response_str)