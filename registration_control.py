import pickle
from tkinter import *
import cv2
from PIL import Image,ImageTk
import os
import data_flow_controle
import tkinter as tk
from tkinter import messagebox
import openpyexcel
###############################################################################################################
#The camera class provide Camera interface To store The photo of Registed person
##############################################################################################################
class Reg_Camera(Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.image = None
        self.minsize(width=720, height=540)
        self.configure(bg="#2e7e99")
        self.title("Camera")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.frame = None
        self.label = None
        self.take_frame = None
        self.cancel = None
        self.register = None
        self.img_default_location()

    def camera_frame(self):
        came_frame=LabelFrame(self,bg="yellow")
        came_frame.pack()
        self.label_came=Label(came_frame,bg="yellow")
        self.label_came.pack()
        self.capture = cv2.VideoCapture(0)


    def camera_controle(self):
        while True:
            condition, frames = self.capture.read()
            if condition == False:
                break
            # frame = cv2.resize(frames,(0,0),None,0.25,0.25)
            frame = cv2.cvtColor(frames, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame,1)
            img_array = Image.fromarray(frame)
            frame = ImageTk.PhotoImage(img_array)
            self.image = img_array
            self.label_came.frame = frame
            self.label_came['image'] = frame
            self.frame = frame
            self.update()
            if cv2.waitKey(1) == 13:
                break
        self.capture.release()
        cv2.destroyAllWindows()


    def capture_photo(self):
        self.img_default_location()
        self.label_came['image'] = self.frame
        self.capture = cv2.VideoCapture()
        file = open("pathsfolder/reg.data", "rb")
        teacher_data = pickle.load(file)
        teacher_data[0]=teacher_data[0].upper()+" "+str(teacher_data[2])
        self.name = f'{teacher_data[0]}.jpg'
        read_myfile = open("pathsfolder/address2.data", "rb")
        images_folder = pickle.load(read_myfile)
        self.image.save(f'{images_folder}/{self.name}')
        self.cancel['state'] = NORMAL
        self.register['state'] = NORMAL
        self.take_frame['state'] = DISABLED

    def cancel_photo(self):
        self.take_frame['state'] = NORMAL
        self.cancel['state'] = DISABLED
        self.register['state'] = DISABLED
        self.capture = cv2.VideoCapture(0)
        read_myfile = open("pathsfolder/address2.data", "rb")
        reg_images_folder = pickle.load(read_myfile)
        os.remove(f'{reg_images_folder}/{self.name}')
        self.capture = cv2.VideoCapture(0)
        self.camera_controle()

    def save_photo(self):
        self.camera_controle()

    def img_default_location(self):
        Images_folder = None
        work_dir = os.getcwd()
        all_folders = os.listdir(work_dir)
        if "Images" not in all_folders:
            Images_folder = os.mkdir(f"{work_dir}/Images")
        elif "Images" in all_folders:
            Images_folder = f"{work_dir}/Images"
        myfile = open("pathsfolder/address2.data", "wb")
        pickle.dump(Images_folder, myfile)
        self.encode_default_location()

    def encode_default_location(self):
        work_dir = os.getcwd()
        all_folders = os.listdir(work_dir)
        if "Encodes" not in all_folders:
            Images_folder = os.mkdir(f"{work_dir}/Encodes")


    def store_registration(self):
        Data_Manager = data_flow_controle.Data_Manager()
        Data_Manager.store_registration()
        self.destroy()

    def build_buttons(self):
        self.button_style()
        fram_buttons = Frame(self, bg="#2e7e99")
        fram_buttons.pack(pady=10)
        self.take_frame = Button(fram_buttons,image=self.label.img,width=155,height=50, text="Take Photo",compound=CENTER,command=self.capture_photo, bg="#2e7e99",fg="white",
                            font=("Arial black", 10),borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff")
        self.take_frame.pack(side=LEFT, padx=10)
        self.cancel = Button(fram_buttons,state=DISABLED,image=self.label.img,width=155,height=50,text="Cancel",compound=CENTER,command=self.cancel_photo, bg="#2e7e99",fg="white", font=("Arial black", 10),borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff")
        self.cancel.pack(side=LEFT, padx=10)
        self.register = Button(fram_buttons,state=DISABLED,image=self.label.img,width=155,height=50,text="Register",compound=CENTER,command=self.store_registration, bg="#2e7e99",fg="white",
                          font=("Arial black", 10),borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff")
        self.register.pack(side=LEFT, padx=10)

    def button_style(self):
        img = PhotoImage(file="Buttons/Search button.png")
        self.label = Label(image=img)
        self.label.img = img

    def on_close(self):
        self.capture = cv2.VideoCapture()
        self.destroy()
################################################################################################################################################
#This is the registration entres interface for geting information of Teachers
################################################################################################################################################
class registration_interface(Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.name = None
        self.lastname = None
        self.father_name = None
        self.id_number = None
        self.subject = None
        self.phone_number = None
    ####################################################
    def whole_reg_interface(self):
        self.minsize(width=720, height=540)
        self.configure(background="#2e7e99")
        self.title("Teacher Registration")
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.camera_on = False
        # self.resizable(False, False)
        self.headings()
        self.sub_frames()
        self.set_entry_name()
        self.create_entry()
        self.creat_buttons()
        self.label = None
        # self.default_file()
    #########################################################
    def headings(self):
        self.heading_of_registration =Label(self,text="Teacher Registration",font=("Arial Black",30),bg="#2e7e99",fg="#F9F9F9")
        self.heading_of_registration.pack()

    def sub_frames(self):
        """self.entres_frame = Frame(self, bg="#34568B")
        self.entres_frame.pack()"""
        self.frame_of_labels_and_entres = Frame(self, bg="#2e7e99")
        self.frame_of_labels_and_entres.pack(pady=40)
        self.button_frame = Frame(self, bg='#2e7e99', padx=40)
        self.button_frame.pack()

    def create_entry(self):
        name = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        name.grid(row=1, column=2, pady=10)
        self.name = name
        name.focus()
        father_name = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        father_name.grid(row=2, column=2, pady=10)
        self.father_name = father_name
        id_number = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        id_number.grid(row=3, column=2, pady=10)
        self.id_number = id_number
        subject = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        subject.grid(row=4, column=2, pady=10)
        self.subject = subject
        phone_number = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        phone_number.grid(row=5, column=2, pady=10)
        self.phone_number = phone_number


    def set_entry_name(self):
        Label(self.frame_of_labels_and_entres, text="NAME", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=1,
                                                                                                             column=1)
        Label(self.frame_of_labels_and_entres, text="FATHER NAME", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(
            row=2, column=1)
        Label(self.frame_of_labels_and_entres, text="ID NO", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=3,
                                                                                                             column=1)
        Label(self.frame_of_labels_and_entres, text="SUBJECT", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=4,
                                                                                                               column=1)
        Label(self.frame_of_labels_and_entres, text="PHONE", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=5,
                                                                                                             column=1)
    def get_entres(self):
        Data_Manager = data_flow_controle.Data_Manager()
        Data_Manager.name = self.name.get()
        Data_Manager.father_name = self.father_name.get()
        Data_Manager.subject = self.subject.get()
        Data_Manager.id_number = int(self.id_number.get())
        Data_Manager.phone_number = int(self.phone_number.get())
        Data_Manager.saving_registration()

    def attendance_file_reader(self):
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        workbook.save(address)
        return workbook

    def web_came(self):
        name = self.name.get()
        father_name = self.father_name.get()
        id_number = self.id_number.get()
        subject = self.subject.get()
        phone_number = self.phone_number.get()
        all_ids = []
        old_list = []
        file = open("pathsfolder/reg.data", "rb")
        teacher_data = pickle.load(file)
        txtfile = open("pathsfolder/address3.data", "rb")
        reg_file = pickle.load(txtfile)
        workbook = openpyexcel.load_workbook(reg_file)
        sheet = workbook.worksheets[0]
        row= sheet.max_row
        colums = sheet.max_column
        attend_book = self.attendance_file_reader()
        attend_sheet = attend_book["Registration dates"]
        rows=attend_sheet.max_row
        cols=attend_sheet.max_column
        for r in range(2, rows + 1):
            for c in range(1, cols + 1):
                if c == 2:
                    id_no = str(attend_sheet.cell(r, c).value)
                    old_list.append(id_no)

        for r in range(2,row+1):
            for c in range(1,colums+1):
                if c == 3:
                    all_ids.append(str(sheet.cell(r,c).value))

        if name == "" or father_name == "" or id_number == "" or subject == "" or phone_number == "":
            messagebox.showinfo("info","Please fill remaining field first!")
        elif id_number in all_ids:
            messagebox.showinfo("info","The IDNO is already register!")
        elif id_number in old_list:
            messagebox.showinfo("info", "You cannot use This ID.NO in this year\nbecause This ID have old record!")
        elif id_number != "" or phone_number !="":
            try:
                id_number = int(self.id_number.get())
                phone_number = int(self.phone_number.get())
                self.grab_release()
                self.withdraw()
                self.get_entres()
                self.camera_on = True
                self.Reg_Camera = Reg_Camera(self)
                self.Reg_Camera.camera_frame()
                self.Reg_Camera.build_buttons()
                self.Reg_Camera.camera_controle()
                self.Reg_Camera.mainloop()
            except:
                messagebox.showinfo("info", "id number and phone number must be contain by number!")

    def clear_entres(self):
        self.name.delete(0, END)
        self.father_name.delete(0,END)
        self.subject.delete(0,END)
        self.id_number.delete(0,END)
        self.phone_number.delete(0,END)
        self.name.focus()

    def creat_buttons(self):
        self.button_style()
        Button(self.button_frame,image=self.label.img,width=155,height=50,text="Cancel",bg="#2e7e99",fg="#FFFFFF",compound=CENTER,
               command=self.clear_entres,pady=3,font=("Arial black",10),borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff").grid(row=6,column=2,padx=60)
        Button(self.button_frame,image=self.label.img,width=155,height=50,text="Next", bg="#2e7e99", fg="#FFFFFF",compound=CENTER,
               command=self.web_came, pady=3, font=("Arial black", 10),borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff").grid(row=6, column=4, padx=12)

    def button_style(self):
        img = PhotoImage(file="Buttons/Search button.png")
        self.label = Label(image=img)
        self.label.img = img

    def on_close(self):
        self.destroy()
        if self.camera_on == True:
            self.Reg_Camera.capture = cv2.VideoCapture()
            self.Reg_Camera.destroy()

    ###################################################################################################################
    ###################################################################################################################
