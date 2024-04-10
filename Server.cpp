#include "thread.h"
#include "socketserver.h"
#include <algorithm>
#include <stdlib.h>
#include <time.h>
#include "Semaphore.h"
#include <list>
#include <vector>
#include <thread>
#include <fstream>

using namespace Sync;
using namespace std;

class SocketThread : public Thread
{
private:
	Socket &socket; // reference to connected socket.
	ByteArray data; // byte array for the data from the client

	int chatRoomNum;
	int port;
	bool &flag;
	vector<SocketThread *> &socketThreadsHolder; // holder for SocketThread pointers.

public:
	SocketThread(Socket &socket, vector<SocketThread *> &clientSockThr, bool &flag, int port) : socket(socket), socketThreadsHolder(clientSockThr), flag(flag), port(port)
	{
	}

	~SocketThread()
	{
		this->terminationEvent.Wait();
	}

	Socket &GetSocket()
	{
		return socket;
	}

	const int GetChatRoom()
	{
		return chatRoomNum;
	}

	virtual long ThreadMain()
	{
		string stringPort = to_string(port);
		Semaphore clientBlock(stringPort); // semaphore generated on each SocketThread

		try
		{
			socket.Read(data); // read data from the socket
			string chatRoomString = data.ToString();
			chatRoomString = chatRoomString.substr(1, chatRoomString.size() - 1);
			chatRoomNum = stoi(chatRoomString);
			cout << "New Chat Room number: " << chatRoomNum << endl;

			while (!flag)
			{
				int socketResult = socket.Read(data);

				if (socketResult == 0)
					break; // if the socket is closed on the client side, terminate this socket thread.

				string recv = data.ToString();

				if (recv == "TYPING")
				{
					// Broadcast "is typing" notification to all other clients in the same room
					for (int i = 0; i < socketThreadsHolder.size(); i++)
					{
						SocketThread *clientSocketThread = socketThreadsHolder[i];
						if (clientSocketThread->GetChatRoom() == chatRoomNum && clientSocketThread != this)
						{
							Socket &clientSocket = clientSocketThread->GetSocket();
							ByteArray sendBa("Someone is typing...");
							clientSocket.Write(sendBa);
						}
					}
				}
				if (recv == "shutdown\n")
				{
					clientBlock.Wait(); // signal the semaphore to prevent other threads accesssing the socket

					socketThreadsHolder.erase(remove(socketThreadsHolder.begin(), socketThreadsHolder.end(), this), socketThreadsHolder.end()); // iterator to remove socket

					clientBlock.Signal();
					cout << "A client is shutting off from our server. Erase client!" << endl;
					break;
				}

				if (recv[0] == '/')
				{ // a forward slash is appended as the first character to change the chat room number.

					string stringChat = recv.substr(1, recv.size() - 1);
					chatRoomNum = stoi(stringChat);
					cout << "A client joined room " << chatRoomNum << endl;
					continue;
				}

				if (recv.substr(0, 4) == "FILE")
				{ // Check if the message is a file upload
					size_t pos = recv.find('\0', 4);
					if (pos != string::npos)
					{
						string filename = recv.substr(4, pos - 4);
						string file_data = recv.substr(pos + 1);
						// Broadcast the filename and file data to all clients in the chatroom
						for (auto &clientThread : socketThreadsHolder)
						{
							if (clientThread->GetChatRoom() == chatRoomNum)
							{
								clientThread->GetSocket().Write("FILE " + filename + "\n" + file_data);
							}
						}
					}
					continue;
				}

				clientBlock.Wait(); // call .Wait() so that the thread can enter the critical section(being the socket)

				for (int i = 0; i < socketThreadsHolder.size(); i++)
				{ // iterate through all SocketThreads to send message to clients in the same room

					SocketThread *clientSocketThread = socketThreadsHolder[i];
					if (clientSocketThread->GetChatRoom() == chatRoomNum)
					{
						Socket &clientSocket = clientSocketThread->GetSocket();
						ByteArray sendBa(recv);
						clientSocket.Write(sendBa);
					}
				}

				clientBlock.Signal(); // signal to allow other threads to enter critical section.
			}
		}
		catch (string &s)
		{ // catch string exceptions
			cout << s << endl;
		}
		catch (exception &e)
		{ // catch other exceptions
			cout << "A client has abruptly quit their messenger app!" << endl;
		}
		cout << "A client has left from a chat room!" << endl;
	}
};

class ServerThread : public Thread
{
private:
	SocketServer &server; // reference to socket server.

	vector<SocketThread *> socketThrHolder; // vector for holding all socketThreads

	int port;
	int numberRooms;

	// Flag for termination.
	bool flag = false;

public:
	ServerThread(SocketServer &server, int numberRooms, int port)
		: server(server), numberRooms(numberRooms), port(port)
	{
	}

	~ServerThread() // Cleanup
	{
		for (auto thread : socketThrHolder) // iterate through each socket
		{
			try
			{
				// Close the socket.
				Socket &toClose = thread->GetSocket();
				toClose.Close();
			}
			catch (...)
			{
			}
		}
		vector<SocketThread *>().swap(socketThrHolder);
		flag = true;
	}

	virtual long ThreadMain()
	{
		while (true)
		{
			try
			{
				string stringPortNum = to_string(port);
				cout << "Waiting on a client to join" << endl;

				Semaphore serverBlock(stringPortNum, 1, true); // ServerThread is the main owner of the semaphore

				string allChats = to_string(numberRooms) + '\n'; // front-end receives number of chats through socket.

				ByteArray allChats_conv(allChats); // byte array conversion for number of chats.

				Socket sock = server.Accept(); // wait for a client socket connection

				sock.Write(allChats_conv); // send number of chats.
				Socket *newConnection = new Socket(sock);

				Socket &socketReference = *newConnection; // pass a reference to this pointer into a new socket thread.
				socketThrHolder.push_back(new SocketThread(socketReference, ref(socketThrHolder), flag, port));
			}

			catch (string error) // catch string-thrown exception.
			{
				cout << "ERROR: " << error << endl;
				return 1;
			}
			catch (TerminationException terminationException) // In case of unexpected shutdown or events
			{
				cout << "Server has shut down, clients have been terminated" << endl;
				return terminationException;
			}
		}
	}
};

int main(void)
{

	int port = 3005;
	int rooms = 20; // max number of chat rooms for the server.

	cout << "Chat Room Project - Server" << endl
		 << "Type done to terminate the server and clients" << endl;

	SocketServer server(port); // Create socket server.

	ServerThread st(server, rooms, port); // Initiate ServerThread for server operations

	// This will wait for input to shutdown the server
	FlexWait cinWaiter(1, stdin);
	cinWaiter.Wait();
	cin.get();

	// Shut down and clean up the server
	server.Shutdown();
}
