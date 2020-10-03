---------
Devin Suy
---------
Contact : DevinSuy@gmail.com

Peer To Peer Networking
-----------------------


How does the client discover other clients on the network?
----------------------------------------------------------
	- Any given node attempting to go "online" starts by running Address Resolution Protocol, obtaining a list
	  of hosts on the given network. This list is filtered down to just those on the network that are dynamic
	  which becomes the nodes "potential peers" list.
	  
	- The initializing node then attempts to establish a socket connection with each host on the potential peers
	  list, timing out if not accepted. If the node suceeds in establishing a connection with one of the potential
	  hosts, it maps the address -> socket, storing it in self.peers {}
	
		- The initializing node then requests initialization data from the accepting node that accepted it's connection
		  which includes a list of known peers on the network (we did not complete the exhaustive search of potential
		  peers, stopping after we were accepted). If the list of known peers (excluding the initializing node) is not
		  empty a socket connection is also established to each one of the peers on the list and stored in self.peers {}
		
		- The accepting node also transmits a distributed file hash {} to the initializing node where
		  file name maps -> list where [0] : SHA-256 Hash of the file, [1] : last modified time (st_mtime), [2] : address of the node who logged this entry
		  
	- In the event that the potential peers list is exhausted without establishing a connection, the initializing node
	  creates the network and copies its local file hash {} into its copy of the distributed file hash {}, switching into "server mode"
	  moving into serving requests once atleast one peer has attempted to join the network, at which point it will send its copy
	  of the distributed file hash {} and help initialize it. Then it moves to serve requests to the node until receiving a "done" message.
	  At which point it will switch into "client mode" to perform file synchronization as the other node will switch into server mode
	  to replace it and process requests until receiving a done message. (See the messaging protocol below)
	  
		# Communication Protocol:
		# -----------------------
		# First message is the type, followed by a ":", followed by the size of the data in the next message

		#   hash (corresponds to the distributed file hash {})
		#   peer (corresponds to the addresses of the other peers on the network)
		#   filereq (request a file, the file name follows the ":" for this message type)

		#   file (send a requested file, the file size is also followed by a
		#       second ":" and then the file's last modification time) followed by a
		#       third ":" and then a False if the file is encoded or True if it is not

		#   time (send the last_change_time to the client)
		#   done (mark the end of a file sync, notifies that the server node may now switch into client mode and sync)

		# The following messages (if applicable) are the requested bytes until all of the data has been transmitted
	
	
How does the client deal with files of the same name, but different contents? Different timestamps?
---------------------------------------------------------------------------------------------------
	- Each time a file is modified locally by a node, it syncs its local file hash {} with the distributed file hash {},
	  merging the two and resolving conflicts by choosing the most recently modified version of a file 
	  (by using os.utime to preserve st_mtime), updating the log in the distributed file hash {} as necessary.
	  
	- When performing a local sync, each file in the "SyncFolder/" directory is run through a SHA-256 hash and compared
	  to the hash stored in the file hash {}, inconsistencies between indicate modification of a file since the previous sync. 
	  Depending on the modification times a node will decide to either: 
		- Retain its local copy -> update the distributed file hash {} entry in addition to logging its own address with it, 
		  update its last_modified_time since a change was detected. Once switching into server mode other nodes will 
		  request it's copy of the file hash {} followed by the modified file and any others needed.
		- Overwrite its local copy -> requesting the most recent version of the file from the peer who logged the
		  entry into the file hash {} for that file 
		- Delete a file present locally that is no longer present in the distributed version of the table
		- Request a file not present locally that is presented in the distributed version
	
	
3. How does the client determine which files to sync in which order
-------------------------------------------------------------------
	- Each node also contains a self.last_change_time attribute that is set to time.time() whenever a file is 
	  detected to have been added/deleted/modified. On a sync operation for a given node, it requests the last_change_time
	  of each one of its peers until the node with the most recently changes has been identified. This identified node is 
	  requested to send over its copy of the distributed file hash {} and synchronization begins in accordance to this node,
	  resolving conflicts and adding entries for merges as necessary.
	  
	- Synchronization is performed in "client mode" and a given node will transition into "server mode" after notifying that
	  it has completed its synchronization.
	 
