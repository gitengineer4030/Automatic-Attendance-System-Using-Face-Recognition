import os
from tkinter import *
import pickle
import openpyexcel
from tkinter import messagebox

class Unregister_interface(Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.wm_minsize(width=720, height=548)
        self.wm_resizable(False,False)
        self.title("Remove Registration")
        self.configure(bg="#2e7e99")
        self.heading()
        self.main_sub_frame = None
        self.reg_list = []
        self.name_list_box = None
        ##########################################################
        self.sub_frames()
        self.search_bar()
        self.record_name_list()
        self.take_registration()
        self.binding_key_list()
        ##########################################################

    def heading(self):
        self.heading_of_registration = Label(self, text="Remove Teacher Registration", font=("Arial Black", 30), bg="#2e7e99",fg="#F9F9F9")
        self.heading_of_registration.pack()

    def sub_frames(self):
        self.main_sub_frame = Frame(self,bg="#2e7e99")
        self.main_sub_frame.pack(pady=170)

    def search_bar(self):
        search_bar_frame = Frame(self.main_sub_frame,bg="#2e7e99")
        search_bar_frame.pack(pady=20)
        search_bar_name=Label(search_bar_frame,bg="#2e7e99",text="Enter ID.NO  ",font=("Arial Black",12),fg="white")
        search_bar_name.pack(side=LEFT)
        img = PhotoImage(file="Buttons/Search button.png")
        label = Label(image=img,width=20)
        label.img = img
        seach_button = Button(search_bar_frame,image=label.img,compound=CENTER,width=155,height=50,text="Delete Registration", font=("Arial black", 10), command=self.remove_registration_data,borderwidth=0,border=0,bg='#2e7e99',fg="white",activebackground="#2e7e99",activeforeground='#00ffff')
        seach_button.pack(side=RIGHT,padx=20)
        self.id_no=Entry(search_bar_frame, width=25, font=("Arial Black", 12),bg="#D8FCC9",background="white")
        self.id_no.pack(side=RIGHT)

    def remove_registration_data(self):
        selected_id=self.id_no.get()
        selected_id=selected_id.upper()
        name_id= selected_id.split(" ")
        namelen = len(name_id)
        name_id = name_id[namelen-1]
        file = open("pathsfolder/address3.data", "rb")
        reg_file = pickle.load(file)
        work_file = openpyexcel.load_workbook(reg_file)
        sheet = work_file.worksheets[0]
        rows = sheet.max_row
        columns = sheet.max_column
        for r in range(2,rows+1):
            for c in range(1,columns+1):
                if c == 3:
                    value = str(sheet.cell(r, c).value)
                    if value == name_id:
                        check=messagebox.askyesno("Deleting Data Alert","Are you sure you want to unregister This person!")
                        if check == 1:
                            sheet.delete_rows(r, 1)
                            work_file.save(reg_file)
                            self.remove_photo(selected_id)

    def remove_photo(self,selected_id):
        image_folder=os.listdir("Images/")
        encoding_folder = os.listdir("Encodes/")
        if f"{selected_id}.jpg" in image_folder:
            print("yes images is found!")
            os.remove(f'Images/{selected_id}.jpg')
            if f"{selected_id}.npy" in encoding_folder:
                os.remove(f"Encodes/{selected_id}.npy")
        self.remove_selected_items()

    def remove_selected_items(self):
        self.id_no.delete(0,END)
        selected_name = self.name_list_box.curselection()
        item_select = int(selected_name[0])
        self.name_list_box.delete(item_select)

    def record_name_list(self):
        self.name_list_box=Listbox(self.main_sub_frame,font=("Arial Black",10),width=40)
        self.name_list_box.pack()

    def get_update(self,data):
        self.name_list_box.delete(0,END)
        for nameid in data:
            self.name_list_box.insert(END,nameid)

    def fill_entry(self,event):
        self.id_no.delete(0,END)
        name = self.name_list_box.get(ACTIVE)
        self.id_no.insert(0,name)

    def take_registration(self):
        reg_list = []
        file = open("pathsfolder/address3.data", "rb")
        reg_file=pickle.load(file)
        work_file = openpyexcel.load_workbook(reg_file)
        sheet = work_file.worksheets[0]
        rows = sheet.max_row
        columns = sheet.max_column
        for r in range(2,rows+1):
            for c in range(1,columns+1):
                if c == 1:
                    self.reg_list.append(sheet.cell(r,c).value+" "+str(sheet.cell(r,3).value))
                    reg_list=self.reg_list
        self.get_update(reg_list)

    def check(self,event):
        typed = self.id_no.get()
        if typed == "":
            data = self.reg_list
        else:
            data = []
            for idname in self.reg_list:
                if typed.lower() in idname.lower():
                    data.append(idname)
        self.get_update(data)

    def binding_key_list(self):
        self.name_list_box.bind("<<ListboxSelect>>", self.fill_entry)
        self.id_no.bind("<KeyRelease>",self.check)

"""if __name__ == '__main__':
    Unregister_interface = Unregister_interface()
    Unregister_interface.start_ui()
    Unregister_interface.mainloop()"""