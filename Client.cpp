#include <csignal>
#include "thread.h"
#include "socket.h"
#include <iostream>
#include <stdlib.h>
#include <time.h>

using namespace Sync;
using namespace std;

int main(void)
{
    try {
        // Welcome the user 
        std::cout << "SE3313 Lab 3 Client" << std::endl;

        // Create our socket
        Socket socket("127.0.0.1", 3005);
        
        socket.Open();
        
        while (true){
            
            //get user input 
            cout << "Enter a string to reverse it, send 'done' to shutdown client" << endl;
            string data;
            cin >> data;
            
            //add string to a bytearray 
            ByteArray sendData(data);
            
            //if client is done, shut down server and clean up socket
            if (data == "done"){
                cout << "Shutting down" << endl;
                socket.Write(sendData);// send to close clientThread
                
                // close socket
                socket.Close();
                break;
                
            } else {
                
                //send in byte array
                socket.Write(sendData);

                //receive the response
                ByteArray response;
                socket.Read(response);
                
                //convert response to string
                string newString = response.ToString();
                
                //check for kill command from serverThread 
                if (newString == "killConfirmed") {
                    cout << "Terminating, server closed" <<endl;
                    break;
                }
                //output response, should be reversed format
                cout << newString << endl;
            } 
        }

        socket.Close();

    } catch (const std::string& e) {
        std::cerr << "Caught exception: " << e << std::endl;
    }

    return 0;
}
