from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
from datetime import datetime
import tkinter.filedialog
import tkinter.ttk as ttk
BUFSIZ = 4096

# Define your color scheme
background_color = "#ffffff"  # Dracula theme background color
foreground_color = "#000000"  # Dracula theme foreground color
button_color = "#2596be" # Dracula theme button color

class AutocompleteEntry(tkinter.Entry):
    def __init__(self, autocomplete_list, *args, **kwargs):
        tkinter.Entry.__init__(self, *args, **kwargs)
        self.autocomplete_list = autocomplete_list
        self.var = kwargs.get('textvariable')  # Access 'textvariable' as a keyword argument
        if self.var is None:
            self.var = tkinter.StringVar()
        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Return>", self.selection)
        self.bind("<Up>", self.up)
        self.bind("<Down>", self.down)
        self.lb_up = False

    def changed(self, name, index, mode):
        if self.var.get() == '':
            self.lb_up = False
            self.lb.destroy()
        else:
            words = self.var.get().split(' ')
            if words:
                pattern = words[-1].lower()
                self.matches = [w for w in self.autocomplete_list if w.lower().startswith(pattern)]
                if self.matches:
                    if not self.lb_up:
                        self.lb = tkinter.Listbox()
                        self.lb.bind("<Double-Button-1>", self.selection)
                        self.lb.bind("<Right>", self.selection)
                        self.lb.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
                        self.lb_up = True
                    self.lb.delete(0, tkinter.END)
                    for w in self.matches:
                        self.lb.insert(tkinter.END, w)
                else:
                    if self.lb_up:
                        self.lb.destroy()
                        self.lb_up = False
        

    def selection(self, event):
        if self.matches:
            selected_word = self.lb.get(tkinter.ACTIVE)
            self.var.set(selected_word)
            self.lb.destroy()
            self.lb_up = False
            self.icursor(tkinter.END)

    def up(self, event):
        if self.matches:
            current_selection = self.lb.curselection()
            if current_selection:
                self.lb.selection_clear(current_selection)
                if current_selection[0] > 0:
                    self.lb.selection_set(current_selection[0] - 1)
                    self.lb.see(current_selection[0] - 1)

    def down(self, event):
        if self.matches:
            current_selection = self.lb.curselection()
            if current_selection:
                self.lb.selection_clear(current_selection)
                if current_selection[0] < self.lb.size() - 1:
                    self.lb.selection_set(current_selection[0] + 1)
                    self.lb.see(current_selection[0] + 1)

def upload_file():
    filename = tkinter.filedialog.askopenfilename()
    if filename:
        with open(filename, 'rb') as f:
            while True:
                file_data = f.read(BUFSIZ)
                if not file_data:
                    break
                client_socket.send(b'FILE' + filename.encode() + b'\0' + file_data)
                # client_socket.send(b'FILE' + filename.encode() + b'\0')


def receive():
    while True:
        try:
            msg = client_socket.recv(BUFSIZ)
            if msg.startswith(b"FILE "):
                pos = msg.find(b'\0')
                if pos != -1:
                    filename = msg[5:pos].decode()
                    file_data = msg[pos+1:]
                    with open(filename, 'ab') as f:
                        f.write(file_data)
                    msg_list.insert(tkinter.END, f"Received file chunk: {filename}")
                else:
                    msg_list.insert(tkinter.END, msg.decode("utf8"))
            else:
                msg_list.insert(tkinter.END, msg.decode("utf8"))
        except OSError:  # Possibly client has left the chat.
            break

def send(event=None): 
    msg = my_msg.get()
    my_msg.set("")      
    global current_room
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if msg == "{quit}":
        client_socket.send(bytes(f'[{timestamp}] {my_username.get()} has closed OS Messenger App!', "utf8"))
        client_socket.close()
        top.quit()
        return
    client_socket.send(bytes(f'[{timestamp}] {my_username.get()}: {msg}', "utf8"))

def on_closing(event=None):
    my_msg.set("{quit}") 
    send()

def change_room(): 
    global current_room
    current_room = ((chatRoomSelected.get()).split(' '))[2]
    client_socket.send(bytes("/" + current_room, "utf8"))
    msg_list.delete(0, tkinter.END)
    msg_list.insert(tkinter.END, "You are now in room " + str(current_room))
    msg_list.see(tkinter.END)


number_of_rooms = 0
current_room = 0

top = tkinter.Tk()
top.title("Client App")

# Apply the color scheme to your application
top.configure(bg=background_color)

messages_frame = tkinter.Frame(top) 
my_msg = tkinter.StringVar()  
my_msg.set("")
my_username = tkinter.StringVar()
my_username.set("")

scrollbar = tkinter.Scrollbar(messages_frame)  
msg_list = tkinter.Listbox(messages_frame, height=30, width=100, yscrollcommand=scrollbar.set, bg=background_color, fg=foreground_color)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack() 

username_label = tkinter.Label(top, text="Enter username: ", bg=background_color, fg=foreground_color)
username_label.pack()
username_field = tkinter.Entry(top, textvariable=my_username, bg=background_color, fg=foreground_color)
username_field.pack() 

message_label = tkinter.Label(top, text="Enter message: ", bg=background_color, fg=foreground_color)
message_label.pack()

autocomplete_list = [
    'Hello',
    'How are you?',
    'Goodbye',
    'Thank you',
    'Please',
    'Yes',
    'No',
    'Maybe',
    'Good morning',
    'Good night',
    'See you later',
    'What is your name?',
    'How old are you?',
    'What time is it?',
    'Where are you from?',
    'Nice to meet you',
    'Have a great day',
    'Welcome back',
    'Congratulations',
    'Happy birthday',
    'I agree with you',
    'Could you please repeat that?',
    'I didn’t understand that',
    'Could you please help me?',
    'I’m sorry for the inconvenience',
    'I appreciate your help',
    'I’m looking forward to our next meeting',
    'Take care',
    'Have a safe journey',
    'Good luck',
    'Wishing you all the best'
]
entry_field = AutocompleteEntry(autocomplete_list, top, textvariable=my_msg, width=50)
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send, bg=button_color, fg=foreground_color)
send_button.pack() 

top.protocol("WM_DELETE_WINDOW", on_closing)

HOST = "127.0.0.1" 
PORT = 3005
BUFFER_SIZE = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR) 

first_msg = client_socket.recv(BUFFER_SIZE).decode("utf8") 
number_of_rooms = int(first_msg)
chatRoomSelected = tkinter.StringVar(top)
chatRoomSelected.set("List Of Chat Rooms")
rooms_list = []
for i in range(number_of_rooms): 
    rooms_list.append("Chat Room " + str(i + 1))

# Create a new frame for the chat room selection and the change room button
top_frame = tkinter.Frame(top)
top_frame.pack(side='top', anchor='ne')

# Use a ttk Combobox instead of an OptionMenu
chat_rooms = ttk.Combobox(top_frame, textvariable=chatRoomSelected, values=rooms_list)
chat_rooms.pack(side='top')

# You can set the colors for the Combobox like this:
style = ttk.Style()
style.theme_use('default')
style.configure("TCombobox", fieldbackground=button_color, foreground=foreground_color)

change_button = tkinter.Button(top_frame, text="Change Room", command=change_room, bg=button_color, fg=foreground_color)
change_button.pack(side='top')

upload_button = tkinter.Button(top, text="Upload File", command=upload_file, bg=button_color, fg=foreground_color)
upload_button.pack() 

receive_thread = Thread(target=receive)
receive_thread.start()
top.resizable(width=False, height=False) 
tkinter.mainloop()