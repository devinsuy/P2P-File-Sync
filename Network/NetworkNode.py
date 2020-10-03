# ---------
# Devin Suy
# ---------

from pathlib import Path
from time import sleep
import hashlib
import socket
import os
import sys
import time
import copy
import json
import threading


class NetworkNode:
    BUFFER_SIZE = 4096

    # Communication Protocol:
    # ----------------------
    # First message is the type, followed by a ":", followed by the size of the data in the next message

    #   hash (corresponds to the distributed file hash)
    #   peer (corresponds to the addresses of the other peers on the network)
    #   filereq (request a file, the file name follows the ":" for this message type)

    #   file (send a requested file, the file size is also followed by a
    #       second ":" and then the file's last modification time) followed by a
    #       third ":" and then a False if the file is encoded or True if it is not

    #   time (send the last_change_time to the client)
    #   done (mark the end of a file sync, notifies that the server node may now switch into client mode and sync)

    # The following messages (if applicable) are the requested bytes until all of the data has been transmitted

    def __init__(self):
        self.base_dir = Path("SyncFolder")
        self.port = 5001
        self.ip = socket.gethostbyname(socket.gethostname())  # Store the address of this node
        self.peers = {}  # Maps IPV4 to a list of the corresponding sockets [0] : inbound, [1] : outbound
        self.locked = False  # Mutex lock
        self.distr_hash = {}  # Maps file name -> list where [0] : SHA-256 hash, [1] : file last modified time, [2] : address of the node that pushed the copy
        self.local_hash = {}  # Local version, inconsistencies between the two represent changes in files
        self.last_change_time = -1  # The time that a file change was last detected (add/modify/delete of something in the SyncFolder)

        self.potential_peers = self.get_potential_peers()  # List of all dynamic addresses on the network this node is connected to
        self.local_sync(init_sync=True)
        self.enter_network(self.get_potential_peers())

    # Updates local_hash in accordance with the files currently in SyncFolder
    def local_sync(self, init_sync=False):
        if not init_sync:
            before_sync = copy.deepcopy(self.local_hash)
            self.local_hash.clear()
            local_files = set(os.listdir(self.base_dir))
            for file in local_files:
                self.local_hash[file] = [self.hash_file(file)]  # Map the file name to the generated hash
                self.local_hash[file].append(
                    os.stat(self.base_dir.joinpath(file)).st_mtime)  # Add last modified time metadata
                self.local_hash[file].append(self.ip)  # Add the address logging the entry

            # Local sync detected a change, update last_change_time for this node
            if before_sync != self.local_hash:
                print("---------Change detected---------")
                self.last_change_time = time.time()
        else:
            local_files = set(os.listdir(self.base_dir))
            for file in local_files:
                self.local_hash[file] = [self.hash_file(file)]  # Map the file name to the generated hash
                self.local_hash[file].append(
                    os.stat(self.base_dir.joinpath(file)).st_mtime)  # Add last modified time metadata
                self.local_hash[file].append(self.ip)  # Add the address logging the entry


    # Compares the last modified time between a local copy of a file
    # and the distributed copy, returns True if the local copy is more recent
    def keep_local_copy(self, file_name):
        if self.local_hash[file_name][1] > self.distr_hash[file_name][1]:
            return True
        else:
            return False

    def send_done_msg(self, client_addr):
        client_sock = self.peers[client_addr]
        print("Notifying", client_addr, "that file sync has finished")
        client_sock.sendall("done:none".encode())
        self.retrieve_acknowledgement(client_addr)
        print(client_addr, "has acknowledged and will switch into client mode")

    def sync(self):
        print("\nEntered client mode as", self.ip, "\n")
        self.local_sync()
        last_change_times = {self.ip: float(self.last_change_time)}
        # Map each Node address to the last time it made a change
        for peer in self.peers.keys():
            last_change_times[peer] = float(self.request_change_time(peer))

        # Find the most recently synced node, we will sync our
        # current node in accordance to this
        most_recent_sync = sync_address = -1
        for address, sync_time in last_change_times.items():
            if sync_time > most_recent_sync:
                most_recent_sync = sync_time
                sync_address = address

        # Our current node is the most up to date node, update the file hash log
        if sync_address == self.ip:
            print("Detected our node", self.ip, "to already be the most up to date node on the network")
            print("Syncing file hash with local entries from", self.ip)
            self.distr_hash = copy.deepcopy(self.local_hash)
            self.send_done_msg(list(self.peers.keys())[0])
            return

        # Get the most recent file hash from the most recently synced node
        # (likely very similar to our copy but there may still be changes)
        print("\nDetected", sync_address, "as the most up to date node on the network")
        self.request_file_hash(sync_address)

        # There have been new files created that we don't have locally
        if len(self.distr_hash) > len(self.local_hash):
            files_to_copy = set(self.distr_hash.keys()) - set(self.local_hash.keys())
            # Add a local hash entry and request each of these
            # files since we need them regardless
            for new_file in files_to_copy:
                self.local_hash[new_file] = self.distr_hash[new_file]
                print("Detected new file to copy", new_file)
                self.request_file(new_file, self.distr_hash[new_file][
                    2])  # Request the file from the peer that logged the change into the table
                self.last_change_time = time.time()

        # Files were deleted that we still hold locally, delete them
        elif len(self.local_hash) > len(self.distr_hash):
            files_to_delete = set(self.local_hash.keys()) - set(self.distr_hash.keys())
            print(files_to_delete)
            for file in files_to_delete:
                print("Detected that", file, "was deleted remotely, deleting local copy")
                self.local_hash.pop(file)
                os.remove(self.base_dir.joinpath(file))
                self.last_change_time = time.time()

        # If our file sets still aren't equal we have the same number of files
        # locally as the sync, but they are not the same files, copy the missing files
        # and update the distr table to merge the file sets
        if set(self.local_hash.keys()) != set(self.distr_hash.keys()):
            files_to_copy = set(self.distr_hash.keys()) - set(self.local_hash.keys())
            files_to_merge = set(self.local_hash.keys()) - set(self.distr_hash.keys())

            # Add a local hash entry and request each of these
            # files since we need them regardless
            for new_file in files_to_copy:
                self.local_hash[new_file] = self.distr_hash[new_file]
                print("Detected new file to copy", new_file)
                self.request_file(new_file, self.distr_hash[new_file][
                    2])  # Request the file from the peer that logged the change into the table
                self.last_change_time = time.time()

            # Merge the distr table with files we currently only have present locally
            # so they can be synced by other nodes after
            for file in files_to_merge:
                print("Detected", file, "as not synced, merging file sets")
                self.distr_hash[file] = self.local_hash[file]
                self.last_change_time = time.time()

        # Determine which of our files is out of sync
        for file, file_info in self.distr_hash.items():
            # This file has been modified and does not match our copy
            if self.local_hash[file][0] != file_info[0]:
                print("\nDetected change in", file + ", sync required")
                if self.keep_local_copy(file):  # Our local copy was more recently modified, retain it
                    print("Local copy of", file, "is latest version. Retaining copy and updating hash table")
                    self.distr_hash[file] = self.local_hash[file]
                else:  # Otherwise update the local table and request the newer version
                    self.local_hash[file] = self.distr_hash[file]
                    self.request_file(file, self.distr_hash[file][
                        2])  # Request the file from the peer that logged the change into the table
                self.last_change_time = time.time()

        self.send_done_msg(sync_address)


    # Returns True if a given file should be sent without encoding
    def is_binary_file(self, file):
        path = self.base_dir.joinpath(file)
        try:
            with open(path, "r") as file:
                for _ in file:
                    continue
        # A binary file will throw this error if we try to read it this way
        except UnicodeDecodeError:
            return True

        # We were able to read the file
        return False


    # Check if our local hash matches the current distributed file hash
    # (whether or not our files are the same as those in the synced set)
    def up_to_date(self):
        # We do not have the same amount of files in the local set as the synced set
        if len(self.local_hash) != len(self.distr_hash):
            return False

        # We have the same amount of files, but not the same files
        if set(self.distr_hash.keys()) != set(self.local_hash.keys()):
            return False

        # Check if there was a modification in one of the files since the last sync
        for file, file_hash in self.local_hash.items():
            if file_hash[0] != self.distr_hash[file][0]:
                return False

        # We are up to date with sync!
        return True

        # Generate a SHA-256 hash for the file and return it

    def hash_file(self, file):
        BUFFER_SIZE = 65536  # Avoid loading entire file into memory (could be very big!)
        hash = hashlib.sha256()
        path = self.base_dir.joinpath(file)

        # Pass through the file and generate the hash
        with open(path, "rb") as in_file:
            current_bytes = in_file.read(BUFFER_SIZE)
            while len(current_bytes) > 0:  # Read until the end of the file
                hash.update(current_bytes)
                current_bytes = in_file.read(BUFFER_SIZE)

        return hash.hexdigest()


    # Empty out the socket buffer after transmitting data
    def empty_socket(self, peer_addr):
        peer_sock = self.peers[peer_addr]
        while True:
            try:            # Read until there is nothing to read
                tmp = peer_sock.recv(NetworkNode.BUFFER_SIZE)
            except socket.error:
                break       # Socket is empty


    # Run the Address Resolution Protocol to discover the
    # addresses of hosts on the current LAN
    def get_potential_peers(self):
        table = os.popen('arp -a').read()
        rows = table.split('\n')

        potenial_peers = []
        for row in rows:
            # Peer discovery, our file sync operates in LAN so we are only
            # interested in dynamic addresses on this table (out clients)
            if "dynamic" in row and self.ip not in row:
                address = row[2:]  # Trim off leading white space
                address = address[:address.find(" ")]  # Cut at the end of the address
                potenial_peers.append(address)

        # We simply have a list of dynamic addresses currently on our LAN, it is very
        # likely that many of them are irrelevant and are not peers, further processing needed
        return potenial_peers

    # Utility function that calculates how many buffer passes a
    # read/send will require by performing ceil division of the
    # total size of the message by the size of each message (buffer)
    def get_num_reads(self, num_bytes):
        return -(-num_bytes // NetworkNode.BUFFER_SIZE)

    # Called after sending data, blocks until recieving an
    # acknowledgement that it was recieved successfully
    def retrieve_acknowledgement(self, client_addr):
        client_sock = self.peers[client_addr]
        client_sock.setblocking(1)
        ack = client_sock.recv(2)
        ack = ack.decode()
        if not ack == "**":
            print("ERROR: Retrieved", ack)
            raise SystemError("Failed to receive acknowledgement from", client_addr)
        print("   Acknowledgement recieved from", client_addr)

    def send_acknowledgement(self, peer_address):
        peer_sock = self.peers[peer_address]
        peer_sock.sendall("**".encode())

    # Proceedure to send the file hash dictionary to an initializing peer
    def send_file_hash(self, client_addr):
        client_sock = self.peers[client_addr]
        # Send the initial message
        print("\n" + client_addr + " has requested file hash, preparing to send")
        encoded_hash = str(self.distr_hash)
        encoded_hash = encoded_hash.replace("\'",
                                            "\"").encode()  # Replace single quotes with double so we can easily JSON decode after
        num_bytes = len(encoded_hash)
        client_sock.sendall(("hash:" + str(num_bytes)).encode())

        # Wait to recieve an acknowledgement message before sending
        self.retrieve_acknowledgement(client_addr)

        # Begin sending the distributed hash to the initializing peer
        client_sock.sendall(encoded_hash)
        print("\nFile hash has been sent.")
        self.retrieve_acknowledgement(client_addr)


    # Send the peers list to an initializing node
    def send_peers(self, client_addr):
        client_sock = self.peers[client_addr]
        peer_addresses = list(self.peers.keys())
        peer_addresses.remove(client_addr)  # The client node should not be a peer of itself, remove before sending

        if len(peer_addresses) > 0:
            print("\n" + client_addr + "has requested the current peer list, preparing to send")
            # Serialize by converting into string
            l_str = "["
            for address in peer_addresses:
                l_str += ("\"" + address + "\",")
            l_str = l_str[:-1]  # Trim of trailing comma
            l_str += "]"  # Add close bracket

            encoded_peers = l_str.encode()
            num_bytes = len(encoded_peers)
            client_sock.sendall(("peer:" + str(num_bytes)).encode())  # Send the size of the incoming message
            self.retrieve_acknowledgement(client_addr)

            # Begin transmitting peer list
            client_sock.sendall(encoded_peers)

            self.retrieve_acknowledgement(client_addr)
            print("Peer list successfully sent to", client_addr)
        else:
            client_sock.sendall("peer:0".encode())
            print("Notifying", client_addr, "that there are no other peers on the network currently")
            self.retrieve_acknowledgement(client_addr)


    def send_file(self, client_addr, file_name):
        client_sock = self.peers[client_addr]
        print("\n", client_addr, "has requested", file_name)

        if file_name != "none":
            path = self.base_dir.joinpath(file_name)
            file_size = os.path.getsize(path)

            # First send the file size along with the last modified metadata
            print("   Sending file size of", file_name, "to", client_addr)
            client_sock.sendall(("file:" + str(file_size) + ":" + str(path.stat().st_mtime)).encode())
            self.retrieve_acknowledgement(client_addr)

            # Begin sending the requested file to the client
            with open(path, "rb") as file:
                while True:
                    bytes_read = file.read(NetworkNode.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    client_sock.sendall(bytes_read)
            print("  ", file_name, "sent to", client_addr)
            self.retrieve_acknowledgement(client_addr)


    def send_change_time(self, client_addr):
        client_sock = self.peers[client_addr]
        print("\n" + client_addr, "has requested last_change_time of", self.ip)

        client_sock.sendall(str(self.last_change_time).encode())
        print("   last_change_time sent to", client_addr)
        self.retrieve_acknowledgement(client_addr)


    # Requests the file hash from a node and updates the copy of our current node
    def request_file_hash(self, peer_address):
        peer_sock = self.peers[peer_address]
        print("\nRequesting file_hash from", peer_address)
        peer_sock.sendall("hash:none".encode())

        # Retrieve initial message containing the hash table size
        rcv = peer_sock.recv(NetworkNode.BUFFER_SIZE).decode()
        msg_type, msg_size = rcv.split(":")
        msg_size = int(msg_size)
        self.send_acknowledgement(peer_address)
        print("   Received msg size, sending acknowledgement to", peer_address)

        # Begin receiving message
        msg = bytearray()
        num_read = 0
        while num_read != msg_size:
            if num_read + NetworkNode.BUFFER_SIZE > msg_size:
                rcv = peer_sock.recv(msg_size - num_read)
                num_read += (msg_size - num_read)
            else:
                rcv = peer_sock.recv(NetworkNode.BUFFER_SIZE)
                num_read += NetworkNode.BUFFER_SIZE
            msg.extend(rcv)

        table_str = msg.decode()
        self.distr_hash = json.loads(table_str)
        self.send_acknowledgement(peer_address)
        print("   Received file hash, sending acknowledgement to", peer_address)


    def request_file(self, file_name, peer_address):
        peer_sock = self.peers[peer_address]
        print("\nRequesting", file_name, "from", peer_address)
        peer_sock.sendall(("filereq:" + file_name).encode())

        # Retrieve the file size message, and file last modification time
        # (we preserve this meta data as its used in synchronization)
        rcv = peer_sock.recv(NetworkNode.BUFFER_SIZE).decode()
        print("RCV for file info is:", rcv)
        msg_type, msg_size, mod_time = rcv.split(":")
        msg_size = int(msg_size)
        mod_time = float(mod_time)
        print("   Received file size, sending acknowledgement to", peer_address)
        self.send_acknowledgement(peer_address)

        # Begin receiving file
        msg = bytearray()
        num_read = 0

        peer_sock.settimeout(1)
        print("Receiving", file_name, "from", peer_address + " . . .")
        while True:
            try:
                rcv = peer_sock.recv(NetworkNode.BUFFER_SIZE)
                if len(rcv) == 0:
                    raise Exception(file_name, "download complete")
                msg.extend(rcv)
            except socket.error:
                peer_sock.setblocking(1)
                self.send_acknowledgement(peer_address)
                print("   Received", file_name + ", sending acknowledgement to", peer_address)
                break

        # Write the file locally
        path = self.base_dir.joinpath(file_name)
        with open(path, "wb") as file:
            file.write(msg)
        print("Downloaded file hash for", file_name, "is:", self.hash_file(file_name))

        # Preserve the modification time we received, update the local hash
        os.utime(path, (path.stat().st_atime, mod_time))
        self.local_hash[file_name] = [self.hash_file(file_name), mod_time]


    # Gets the last_change_time of a given Node
    def request_change_time(self, peer_address):
        peer_sock = self.peers[peer_address]
        print("\nRequesting last_change_time from", peer_address)
        peer_sock.sendall("time:none".encode())

        # Receive the sync time message
        sync_time = float(peer_sock.recv(NetworkNode.BUFFER_SIZE).decode())
        self.send_acknowledgement(peer_address)
        print("last_change_time received from", peer_address)

        return sync_time

    def serve_requests(self, client_addr):
        print("\nEntered server mode as", self.ip, "\n")
        client_sock = self.peers[client_addr]

        while True:
            # Retrieve the request from the client
            rcv = client_sock.recv(NetworkNode.BUFFER_SIZE)
            msg_type, msg_data = rcv.decode().split(":")

            # Node is requesting the file hash
            if msg_type == "hash":
                self.send_file_hash(client_addr)

            # Node is requesting a file, send it over preserving modified time metadata
            elif msg_type == "filereq":
                self.send_file(client_addr, msg_data)

            # Node is requesting the last_change_time of the current node, send it
            elif msg_type == "time":
                self.send_change_time(client_addr)

            # Node is requesting initialization, send the current list of peers
            elif msg_type == "init":
                print("\nInitializing peer", client_addr, " . . .")
                self.send_peers(client_addr)

            # Node has finished performing a file sync and is switching into server
            # mode, switch the current node into client mode
            elif msg_type == "done":
                print("\nNotified that", client_addr, "has finished file sync, preparing to sync")
                self.send_acknowledgement(client_addr)
                print("Acknowledgement sent to", client_addr)
                break

            else:
                raise SystemError(self.ip, "received an unknown request of type \"" + msg_type + "\" from", client_addr)


    # Help initialize incoming nodes into the network
    def broadcast(self):
        self.locked = True
        self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast_sock.bind((self.ip, self.port))
        print("[*] Ready to accept peers, broadcasting as ", self.ip)

        self.broadcast_sock.listen(1)
        client_sock, client_addr = self.broadcast_sock.accept()
        client_addr = client_addr[0]  # Discard port

        # Add to our peer list
        self.peers[client_addr] = client_sock
        print("\n[+] Accepted ", client_addr, "as a new peer")
        self.serve_requests(client_addr)


    # Coordinate with the peer to enter the network by recieving the file sync hash
    # as well as information about other peers on the network which we must connect to
    def initialize_node(self, address):
        sock = self.peers[address]
        self.request_file_hash(address)

        sock.sendall("init:none".encode())  # Request initialization data from this node
        # Retrieve initial message containing size of peer list
        rcv = sock.recv(NetworkNode.BUFFER_SIZE).decode()
        msg_type, msg_size = rcv.split(":")
        msg_size = int(msg_size)
        self.send_acknowledgement(address)
        print("   Received msg size, sending acknowledgement to", address)

        if msg_size > 0:
            # Begin receiving message
            msg = bytearray()
            num_read = 0

            while num_read != msg_size:
                if num_read + NetworkNode.BUFFER_SIZE > msg_size:
                    rcv = sock.recv(msg_size - num_read)
                    num_read += (msg_size - num_read)
                else:
                    rcv = sock.recv(NetworkNode.BUFFER_SIZE)
                    num_read += NetworkNode.BUFFER_SIZE
                msg.extend(rcv)
            self.send_acknowledgement(address)
            print("   Received peer list, sending acknowledgement to", address)
            peer_list = json.loads(msg.decode())

            # Establish a connection to each peer on the received peer list
            for address in peer_list:
                peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_sock.connect((address, self.port))
                self.peers[address] = peer_sock  # Save the connection to each peer
        else:
            print("\n   " + address, "has notified that there are currently no other peers on the network")

    # Attempt to establish a connection until we find an address
    # that is one of a valid peer
    def enter_network(self, potential_peers):
        print("Initializing Node @", self.ip)
        print("Potential peers:", potential_peers)
        print("\nAttempting to enter P2P Network . . .")
        accepted = False
        peer_address = peer_sock = None

        # Process our potential peers to enter the network
        for ADDRESS in self.potential_peers:
            try:
                print("   Trying entry @", ADDRESS)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ADDRESS, self.port))
            except:
                print("      Not a valid peer")
                continue

            # Save the address of the initial peer that will initialize
            # our node into network (will send us the distributed table and other peers)
            print("\nConnection accepted by " + ADDRESS + "! Configuring entry . . .")
            peer_address = ADDRESS
            peer_sock = sock
            accepted = True
            break

        if accepted:
            self.peers[peer_address] = peer_sock  # Save the node initializing us as a peer
            self.initialize_node(peer_address)
            self.sync()

            # Main loop for secondary node that enters the network
            while True:
                try:
                    self.serve_requests(list(self.peers.keys())[0])     # Re-enter server mode
                    self.sync()                                         # Re-enter client mode to sync
                except ConnectionResetError:
                    print("Node has left the network")
                    # Node has left the network, rebroadcast
                    self.broadcast()


        # Network hasn't been initialized, this is the first node to enter
        # set up as server mode until client node is initialized
        else:
            print("\nNetwork not yet established, initializing as first node . . .")
            self.distr_hash = copy.deepcopy(self.local_hash)
            self.last_change_time = time.time()

            # Will act as server until notified that client node has finished initializing
            self.broadcast()

            # Main loop for initial node that enters the network
            while True:
                try:
                    self.sync()                                         # Transitions to client mode after
                    self.serve_requests(list(self.peers.keys())[0])     # Re-enter server mode
                except ConnectionResetError:
                    print("Node has left the network")
                    # Node has left the network, rebroadcast
                    self.broadcast()
