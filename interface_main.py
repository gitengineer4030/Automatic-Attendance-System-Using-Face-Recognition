import os
import sys
from tkinter import *
import pickle
import registration_control
import unregister_control
from tkinter import filedialog
from multiprocessing import *
import main
import openpyexcel
import tkinter
from tkinter import ttk
from datetime import datetime
from history_interface import History_management
import history_interface
from tkinter import messagebox
##################################################################################################################################################
##################################################################################################################################################
class Caller_interface(Tk):
    def __init__(self):
        super().__init__()
        self.name = None
        self.dateandtime = None
        self.task_running = False
        self.ids_list = []
        self.label = None
        self.year = datetime.today().strftime("%Y")
        self.default_address_files_creater()
        self.reg_excel_file_creater()
        self.reg_default_file()
        self.attendance_excel_file_creater()
        self.attendance_default_file()


    def on_close(self):
        if self.task_running == True:
            self.task1.kill()
        self.destroy()
        Attendance_taker = main.Attendance_taker()
        Attendance_taker.date_time_saver()

    def stop(self):
        self.start['state'] = NORMAL
        self.task1.kill()
        self.stop.configure(state=DISABLED,bg="#2e7e99")
        Attendance_taker = main.Attendance_taker()
        Attendance_taker.date_time_saver()

    def heading(self):
        head = Label(self,text="Automatic Attendance System",font=("Arial black",30),fg="#FFFFFF",bg="#2e7e99")
        head.pack(pady=30)

    def build_Table(self):
        tree_style = ttk.Style()
        tree_style.configure("Treeview",background="gray17",foreground="white")
        tree_style.configure("Treeview.Heading",font=("Arial black",10),background="gray17")
        tree_frame = Frame(self)
        tree_frame.pack()
        tree_scroll = Scrollbar(tree_frame)
        tree_scroll.pack(side=RIGHT, fill=Y)
        all_columns = ("name","id.no","Attendance",'date','time')
        self.data_tree=ttk.Treeview(tree_frame,show="headings",columns=all_columns,yscrollcommand=tree_scroll.set,height=20)
        tree_scroll.configure(command=self.data_tree.yview)
        self.data_tree.column('name',minwidth=120)
        self.data_tree.column("id.no",minwidth=80)
        self.data_tree.column("Attendance",minwidth=80)
        self.data_tree.column("date",minwidth=100)
        self.data_tree.column("time", minwidth=100)
        #Headings
        self.data_tree.heading('name',text="NAME",anchor=tkinter.W)
        self.data_tree.heading('id.no',text="ID.NO",anchor=tkinter.W)
        self.data_tree.heading("Attendance",text="Attendance",anchor=tkinter.W)
        self.data_tree.heading('date', text="DATE",anchor=tkinter.W)
        self.data_tree.heading('time', text="TIME", anchor=tkinter.W)
        self.data_tree.pack()

    def reg_interfaces(self):
        reg_interface=registration_control.registration_interface(self)
        reg_interface.whole_reg_interface()
        reg_interface.grab_set()

    def unreg_interface(self):
        unregister_interface = unregister_control.Unregister_interface(self)
        unregister_interface.grab_set()

    def cam(self):
        self.start.update()
        self.stop.configure(state=NORMAL,bg='#2e7e99')
        self.start.configure(state=DISABLED,bg='#2e7e99')
        Attendance_taker = main.Attendance_taker()
        img_present=Attendance_taker.image_and_person_name_path_provider()
        if img_present == False:
            sys.exit()
        self.task_running = True
        self.task1 = Process(target=Attendance_taker.came_scanner,daemon=True)
        self.task1.start()

    def data_reciver(self):
        address=open("pathsfolder/address.data","rb")
        file_address=pickle.load(address)
        workbook = openpyexcel.load_workbook(file_address)
        all_sheets = workbook.sheetnames
        month = datetime.today().strftime("%b")
        if month not in all_sheets:
            workbook.create_sheet(month)
        sheet1 = workbook[month]
        row = sheet1.max_row
        colums = sheet1.max_column
        lis = []
        for i in range(2, row + 1):
            for j in range(1, colums + 1):
                lis.append(sheet1.cell(i, j).value)
            name = lis[0]
            id_no = lis[1]
            attendance = lis[2]
            date = lis[3]
            time = lis[4]
            today_date = datetime.today().strftime('%m/%d/%Y')
            if date == today_date:
                if id_no not in self.ids_list:
                    self.ids_list.append(id_no)
                    self.data_tree.insert('', index=i, values=([name, id_no, attendance, date, time]))
            lis.clear()
        self.data_tree.after(300,self.data_reciver)

    ##################################################################################################################
    def reg_excel_file_creater(self):               #These two creat excel file for registration and also save address
        check = os.listdir("Teachers datafile")
        if f"Teachers Registration.xlsx" not in check:
            path = f"Teachers datafile/Teachers Registration"
            file = openpyexcel.Workbook(f"{path}")
            file.save(f"{path}.xlsx")

    def reg_default_file(self):
        self.reg_excel_file_creater()
        current_drive = os.getcwd()
        default_path = f"{current_drive}/Teachers datafile/Teachers Registration.xlsx"
        myfile = open("pathsfolder/address3.data", "wb")
        pickle.dump(default_path, myfile)
    ###################################################################################################################
    def attendance_excel_file_creater(self):
        check = os.listdir("Teachers datafile")
        if f"Teachers data {self.year}.xlsx" not in check:
            path = f"Teachers datafile/Teachers data {self.year}"
            file = openpyexcel.Workbook(f"{path}")
            file.save(f"{path}.xlsx")

    def attendance_default_file(self):
        current_drive = os.getcwd()
        default_path=f"{current_drive}/Teachers datafile/Teachers data {self.year}.xlsx"
        myfile = open("pathsfolder/address.data", "wb")
        pickle.dump(default_path, myfile)
        ############################################################
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        if "Registration dates" not in workbook.sheetnames:
            workbook.create_sheet(title="Registration dates", index=3)
            workbook.save(address)
        if "Sheet" in workbook.sheetnames:
            sheet = workbook["Sheet"]
            workbook.remove(sheet)
            workbook.save(address)

    def location_selector(self):
        self.file_path = filedialog.askopenfilename(title="Select file", initialfile=f"/Teachers datafile/",
                                                    filetypes=(("Microsoft Excel Worksheet", "*.xlsx"),))
        path_slices = self.file_path.split("/")
        silce_of_path_slices = len(path_slices)
        file_name = path_slices[silce_of_path_slices - 1]
        slice_file_name = file_name.split(" ")
        if "Teachers" in slice_file_name and "data" in slice_file_name:
            year = slice_file_name[2].split(".")
            year = year[0]
            if year > self.year or year < self.year and self.file_path != "":
                self.start.configure(state=DISABLED)
                myfile = open("pathsfolder/address.data", "wb")
                pickle.dump(self.file_path, myfile)
            if year == self.year:
                self.start.configure(state=NORMAL)
        else:
            messagebox.showinfo("info","Please chose Teachers data file you chose the wrong file!")

    def history_calling(self):
        His_manage = History_management()
        His_manage.registration_date_backup()
        History_table = history_interface.History_table(self)
        History_table.run_history()
        History_table.grab_set()

    def button_style(self):
        img = PhotoImage(file="Buttons/Search button.png")
        self.label = Label(image=img)
        self.label.img = img
        ##################################################

    def build_buttons(self):
        self.button_style()
        button_frame=Frame(self,bg="#2e7e99")
        button_frame.pack(pady=30)
        self.update()
        Button(button_frame,image=self.label.img, text="Select Location",width=155,height=50, font=("Arial black", 10),compound=CENTER, command=self.location_selector, bg='#2e7e99',
               fg="white",border=0, borderwidth=0,activebackground="#2e7e99",activeforeground="#00ffff").pack(side=LEFT,padx=10)
        Button(button_frame,image=self.label.img,text="Registration",width=155,height=50,font=("Arial black",10),compound=CENTER,command=self.reg_interfaces,bg='#2e7e99',fg="white",borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff").pack(side=LEFT,padx=10)
        Button(button_frame, image=self.label.img, text="Unregister", width=155, height=50, font=("Arial black", 10),compound=CENTER, command=self.unreg_interface, bg='#2e7e99', fg="white", borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff").pack(side=LEFT,padx=10)
        self.start=Button(button_frame,image=self.label.img,text="Start Attendance",width=155,height=50,font=("Arial black",10),compound=CENTER,command=self.cam, bg='#2e7e99', fg="white",borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff")
        self.start.pack(side=LEFT,padx=10)
        self.stop =Button(button_frame,state=DISABLED,image=self.label.img,text="Stop Attendance",width=155,height=50,font=("Arial black",10),compound=CENTER,command=self.stop, bg='#2e7e99', fg="white",borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff")
        self.stop.pack(side=LEFT,padx=10)
        Button(button_frame,image=self.label.img, text="Teachers History",width=155,height=50,font=("Arial black",10),compound=CENTER,command=self.history_calling, bg='#2e7e99', fg="white",borderwidth=0,border=0,activebackground="#2e7e99",activeforeground="#00ffff").pack(side=LEFT,padx=10)

    def default_address_files_creater(self):
        work_dir = os.getcwd()
        all_folders = os.listdir(work_dir)
        if "pathsfolder" not in all_folders:
            path_folder = os.mkdir(f"{work_dir}/pathsfolder")

####################################################################################################################################################
####################################################################################################################################################
if __name__ == '__main__':
    Caller_interface = Caller_interface()
    Caller_interface.configure(bg="#2e7e99")
    photo = PhotoImage(file="Buttons/Teacher.png")
    Caller_interface.iconphoto(False, photo)
    Caller_interface.wm_minsize(width=1080, height=648)
    Caller_interface.title("Teacher today Attendance")
    Caller_interface.protocol("WM_DELETE_WINDOW", Caller_interface.on_close)
    Caller_interface.heading()
    #Caller_interface.seach_bar()
    Caller_interface.build_Table()
    Caller_interface.build_buttons()
    Caller_interface.after(300,Caller_interface.data_reciver)
    Caller_interface.mainloop()
