import socket
import hashlib
import time

import matplotlib.pyplot as plt

entryID = "2021CS11211"
team = "aakubhai"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_host = "vayu.iitd.ac.in"
server_port = 9802
send_reset_request = "SendSize\nReset\n\n"

t1 = time.time()
# flag = True
while True:
    try:
        # print("hello")
        client_socket.sendto(send_reset_request.encode(), (server_host, server_port))
        break
    except:
        print("server is not responding")
        time.sleep(0.1)

response, server_address = client_socket.recvfrom(4096)
rtt = time.time() - t1
response_str = response.decode("utf-8")

client_socket.settimeout(rtt)
data_size = 0

if response_str.startswith("Size: "):
    data_size = int(response_str.split(' ')[1])

size = int(data_size)
print(f"Size: {size}")


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

burst = []
times = []

rtt_list = []
rtt_time_list = []

while offset < size:
    # print("burst size: ", burst_size," offset: ", offset, "len of hash received: ", len(data_hash))
    hash = {}
    hash_check = {}
    requests = 0
    while requests < burst_size:
        num_bytes = min(max_chunk_size, size - offset)
        data_request = f"Offset: {offset}\nNumBytes: {num_bytes}\n\n"
        # print("sending offset :", offset, "at t = ", time.time() - start_time)
        sentx.append(time.time() - start_time)
        senty.append(offset)
        hash[offset] = time.time()
        hash_check[offset] = False
        client_socket.sendto(data_request.encode(), (server_host, server_port))
        # time.sleep(0.01)
        requests += 1
        offset += num_bytes
    # print("burst size requests sent")

    requests_received = 0
    time.sleep(0.01)
    count = 0

    while count <= burst_size:
        burst.append(burst_size)
        times.append(time.time() - start_time)
        count += 1
        try:
            data_response, _ = client_socket.recvfrom(4096)

            # print("came")

            if data_response.decode().startswith("Offset"):  # changed f"Offset: {offset}" to "Offset"
                split_lines = data_response.decode().split('\n\n')
                try:
                    third_line = split_lines[1]
                except:
                    print("dengindi")
                if third_line.startswith("Squished"):
                    pass  # break or pass confusion
                else:
                    data = split_lines[1]
                    offset_line = split_lines[0]
                    # offset_number_received = offset_line[8:-8]
                    off = findOffset(offset_line)

                    receivedx.append(time.time() - start_time)
                    receivedy.append(off)
                    if off in hash:
                        hash[off] = time.time() - hash[off]
                        hash_check[off] = True
                    # print("offset_number_received :", offset_number_received)
                    # print("off :", off )
                    data_hash[off] = data
                    # print("received offset :", off, "at t = ", time.time() - start_time)

                    offsets_received.add(off)
                    requests_received += 1
        except socket.timeout:  # this mean does it wait for 0.1sec for the server
            pass
    rtt_lis = []
    min_rtt = 0.03
    for key in hash_check:
        if hash_check[key]:
            min_rtt = min(min_rtt, hash[key])
            rtt_lis.append(hash[key])
    rtt = 0.8 * rtt + 0.2 * min_rtt
    print("rtt :", rtt)
    client_socket.settimeout(rtt)
    rtt_list.append(rtt)
    rtt_time_list.append(time.time() - start_time)
    if requests_received >= burst_size:
        burst_size += 1
    else:
        burst_size = burst_size // 2

print("burst completed")
print("len of data hash :", len(data_hash))
print("len of offsets received is :", len(offsets_received))

print()
print()

retry_counter = 0
retry_limit = 10000

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
client_socket.settimeout(0.1)
i = 0
checking = 0
print("len of not there :", len(not_there))
# week 1 code maintaining reliability
while i < len(not_there):
    # print("new_offset :", new_offset)
    new_offset = not_there[i]

    try:
        NumBytes = min(size - new_offset, max_chunk_size)
        data_request = "Offset: " + str(new_offset) + "\nNumBytes: " + str(NumBytes) + "\n\n"

        # if len(data_hash)%25==0:
        # print("len of hash :", len(data_hash)*1448, "received time = ", time.time() - start_time)
        sentx.append(time.time() - start_time)
        senty.append(new_offset)
        t0 = time.time()
        client_socket.sendto(data_request.encode(), (server_host, server_port))
        data_response, _ = client_socket.recvfrom(4096)
        # time.sleep(0.01)

        if data_response.decode().startswith(f"Offset: {new_offset}"):
            rtt_list.append(time.time() - t0)
            rtt_time_list.append(time.time() - start_time)
            receivedx.append(time.time() - start_time)
            receivedy.append(new_offset)
            data = data_response.decode().split('\n\n')[1]
            data_hash[new_offset] = data
            checking += 1
            offsets_received.add(new_offset)
            i += 1

    except socket.timeout:
        if retry_counter < retry_limit:
            count += 1
            retry_counter += 1
            # print("Timeout! Retrying...")
            time.sleep(0.01)
            continue
        else:
            print("Timeout! Max retries exceeded. Exiting...")
            time.sleep(0.001)
            break

print("checking :", checking)
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
client_socket.settimeout(0.01)
submit_request = f"Submit: 123@aku\nMD5: " + str(md5_hash) + "\n\n"
client_socket.sendto(submit_request.encode(), (server_host, server_port))

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

# graphs

x_values3 = [x3 for x3 in rtt_time_list]
y_values3 = [y3 for y3 in rtt_list]

plt.figure(figsize=(12, 5))
plt.plot(x_values3, y_values3, marker='o', linestyle='-', color='blue')
plt.xlabel('Time')
plt.ylabel('Round Trip Time')
plt.title('Round Trip Time vs Time')
plt.grid(True)
plt.show()


x_values4 = [x4 for x4 in times]
y_values4 = [y4 for y4 in burst]

plt.figure(figsize=(12, 5))
plt.plot(x_values4, y_values4, marker='o', linestyle='-', color='blue')
plt.xlabel('Time')
plt.ylabel('Burst size')
plt.title('Burst size vs Time')
plt.grid(True)
plt.show()

# overlapping

x_values1 = [x1 for x1 in sentx]
y_values1 = [y1 for y1 in senty]
x_values2 = [x2 for x2 in receivedx]
y_values2 = [y2 for y2 in receivedy]

# Create a figure with one subplot
fig, ax1 = plt.subplots(figsize=(12, 5))

# Plot the data from ax1 and ax2 on the same subplot
ax1.plot(x_values1, y_values1, marker='o', linestyle='-', color='blue', label='Sent Data')
ax1.plot(x_values2, y_values2, marker='o', linestyle='-', color='orange', label='Received Data')

# Customize the subplot
ax1.set_xlabel('time')
ax1.set_ylabel('offset')
ax1.set_title('offset vs time')
ax1.grid()
ax1.legend()

# Adjust the layout to prevent overlapping titles
plt.tight_layout()

# Show the figure with both datasets overlapped
plt.show()