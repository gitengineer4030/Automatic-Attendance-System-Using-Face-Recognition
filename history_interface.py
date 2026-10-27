from datetime import datetime
import pickle
import tkinter
from tkinter import *
from tkinter import ttk
import openpyexcel

class History_management():
    def __init__(self):
        self.present = None
    ############################################################################################################################
    def attendance_file_reader(self):
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        sheet = workbook["Registration dates"]
        sheet.cell(1, 1).value = "NAME"
        sheet.cell(1, 2).value = "IDNO"
        sheet.cell(1, 3).value = "Date of Registration"
        workbook.save(address)
        return workbook

    def registration_date_backup(self):
        name_id = []
        all_name_id = []
        txtfile = open("pathsfolder/address3.data", "rb")
        reg_file = pickle.load(txtfile)
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbookreg = openpyexcel.load_workbook(reg_file)
        regsheet = workbookreg.worksheets[0]
        rows = regsheet.max_row
        cols = regsheet.max_column
        workbook = self.attendance_file_reader()
        sheet = workbook["Registration dates"]
        row = sheet.max_row
        col = sheet.max_column
        ##############################################
        for r in range(2, row + 1):
            for c in range(1, col + 1):
                if c == 2:
                    name_id.append(sheet.cell(r, c).value)
            all_name_id.append(name_id)
            name_id = []
        ##############################################
        for r in range(2, rows + 1):
            for c in range(1, cols + 1):
                name = regsheet.cell(r, 1).value
                id_no = regsheet.cell(r, 3).value
                date_of_reg = regsheet.cell(r, 6).value
            new_list = [id_no]
            if new_list not in all_name_id:
                sheet.append([name, id_no, date_of_reg])
                workbook.save(address)
       #This function is manage date of registration and copy them to the attendance file
    ############################################################################################################################

    def reg_file_details(self,id_no):
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        sheet = workbook.worksheets[0]
        row=sheet.max_row
        col=sheet.max_column
        for r in range(2,row+1):
            for c in range(1,col+1):
                if sheet.cell(r, 2).value == id_no:
                    return sheet.cell(r,3).value

    def month_no_to_month_name(self,month):
        month_by_name = {
            "01":"Jan",
            "02":"Feb",
            "03":"Mar",
            "04":"Apr",
            "05":"May",
            "06":"June",
            "07":"Jul",
            "08":"Aug",
            "09": "Sep",
            "10":"Oct",
            "11":"Nov",
            "12":"Dec"
        }
        return month_by_name[month]


    def file_reader(self,id_num):
        date_of_reg = self.reg_file_details(id_num)
        if date_of_reg is None:
            return
        # Handle datetime objects (Excel date format)
        if isinstance(date_of_reg, datetime):
            day_of_reg = date_of_reg.day
            month_of_reg = str(date_of_reg.month).zfill(2)
        else:
            date_str = str(date_of_reg).strip()
            # Try DD/MM/YYYY or DD/MM format (day first, then month - common in Pakistan)
            parts = date_str.split("/")
            if len(parts) >= 3:
                try:
                    day_of_reg = int(parts[0])      # First part is day
                    month_of_reg = parts[1].zfill(2) # Second part is month
                except ValueError:
                    return
            elif len(parts) == 2:
                try:
                    day_of_reg = int(parts[0])      # First part is day
                    month_of_reg = parts[1].zfill(2) # Second part is month
                except ValueError:
                    return
            else:
                return
        reg_month_name=self.month_no_to_month_name(month_of_reg)
        print(reg_month_name)
        present_list = []
        percentage = 0
        start_date = None
        self.month1_present=self.month2_present=self.month3_present=self.month4_present = self.month5_present = self.month6_present =None
        self.month7_present = self.month8_present=self.month9_present=self.month10_present=self.month11_present=self.month12_present=None
        ######################################################################################################
        self.month1_absence = self.month2_absence = self.month3_absence =self.month4_absence = self.month5_absence = self.month6_absence =None
        self.month7_absence = self.month8_absence = self.month9_absence = self.month10_absence =self.month11_absence =self.month12_absence =None
        ###########################################################################################################
        self.month1_percentage = self.month2_percentage = self.month3_percentage = self.month4_percentage = self.month5_percentage = self.month6_percentage = None
        self.month7_percentage = self.month8_percentage = self.month9_percentage = self.month10_percentage = self.month11_percentage = self.month12_percentage=None
        ########################################################################################################################
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        months= ["Jan","Feb","Mar","Apr","May","June","Jul","Aug","Sep","Oct","Nov","Dec"]
        for month in months:
            if month in workbook.sheetnames:
                sheet = workbook[month]
                row = sheet.max_row
                colums = sheet.max_column
                for r in range(2, row + 1):
                    for c in range(1, colums + 1):
                        if c == 2:
                            if sheet.cell(r, c).value == id_num:
                                present_list.append(sheet.cell(r,c).value)

                present = present_list.count(id_num)
                present_list.clear()
                start_date = 1
                if month == "Jan":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day-start_date
                    self.month1_present = present
                    if days > 0:
                        self.month1_absence = days - present + 1
                    else:
                        self.month1_absence = 0
                    if self.month1_present >= 1:
                        self.month1_percentage = round(self.month1_present / 31 * 100,2)
                elif month == "Feb":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    year = int(datetime.today().strftime("%Y"))
                    day = int(datetime.today().strftime("%d"))
                    if year % 400 == 0 or year % 4 == 0 and year % 100 != 0:
                        if start_date <=day:
                            days = day - start_date
                        else:
                            day = 29
                            days = day - start_date
                    else:
                        if start_date <=day:
                            days = day - start_date
                        else:
                            day = 28
                            days = day - start_date
                    self.month2_present = present
                    if days > 0:
                        self.month2_absence = days - present + 1
                    else:
                        self.month2_absence = 0
                    if self.month2_present >= 1:
                        self.month2_percentage = round(self.month2_present / 31 * 100,2)
                elif month == "Mar":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day-start_date
                    self.month3_present = present
                    if days > 0:
                        self.month3_absence = days - present + 1
                    else:
                        self.month3_absence = 0
                    if self.month3_present >= 1:
                        self.month3_percentage = round(self.month3_present / 31 * 100,2)
                elif month == "Apr":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month4_present = present
                    if days > 0:
                        self.month4_absence = days - present + 1
                    else:
                        self.month4_absence = 0
                    if self.month4_present >= 1:
                        self.month4_percentage = round(self.month4_present / 31 * 100,2)
                elif month == "May":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month5_present = present
                    if days > 0:
                        self.month5_absence = days - present + 1
                    else:
                        self.month5_absence = 0
                    if self.month5_present >= 1:
                        self.month5_percentage = round(self.month5_present / 31 * 100,2)
                elif month == "June":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month6_present = present
                    if days > 0:
                        self.month6_absence = days - present + 1
                    else:
                        self.month6_absence = 0
                    if self.month6_present >= 1:
                        self.month6_percentage = round(self.month6_present / 31 * 100,2)
                elif month == "Jul":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month7_present = present
                    if days > 0:
                        self.month7_absence = days - present + 1
                    else:
                        self.month7_absence = 0
                    if self.month7_present >= 1:
                        self.month7_percentage = round(self.month7_present / 31 * 100,2)
                elif month == "Aug":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month8_present = present
                    if days > 0:
                        self.month8_absence = days - present + 1
                    else:
                        self.month8_absence = 0
                    if self.month8_present >= 1:
                        self.month8_percentage = round(self.month8_present / 31 * 100,2)
                elif month == "Sep":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month9_present = present
                    if days > 0:
                        self.month9_absence = days - present + 1
                    else:
                        self.month9_absence = 0
                    if self.month9_present >=1:
                        self.month9_percentage = round(self.month9_present / 31 * 100,2)
                elif month == "Oct":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month10_present = present
                    if days > 0:
                        self.month10_absence = days - present + 1
                    else:
                        self.month10_absence = 0
                    if self.month10_present >=1:
                        self.month10_percentage = round(self.month10_present / 31 * 100,2)
                elif month == "Nov":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month11_present = present
                    if days > 0:
                        self.month11_absence = days - present + 1
                    else:
                        self.month11_absence = 0
                    if self.month11_present >=1:
                        self.month11_percentage = round(self.month11_present / 31 * 100,2)
                elif month == "Dec":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month12_present = present
                    if days > 0:
                        self.month12_absence = days - present + 1
                    else:
                        self.month12_absence = 0
                    if self.month12_present >=1:
                        self.month12_percentage = round(self.month12_present / 31 * 100,2)
#########################################################################################################################
#  History interface
#########################################################################################################################
class History_table(Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.geometry("850x640")
        self.title("Teacher Attendance History")
        self.configure(bg="#2e7e99")
        self.id_no = None
        self.reg_list = []
        self.table = None
        self.total_presence = 0
        self.total_absence = 0
        self.present = None

    def reg_file_details(self,id_no):
        myfile = open("pathsfolder/address.data", "rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        sheet = workbook.worksheets[0]
        row=sheet.max_row
        col=sheet.max_column
        for r in range(2,row+1):
            for c in range(1,col+1):
                if sheet.cell(r, 2).value == id_no:
                    return sheet.cell(r,3).value

    def check_result(self):
        try:
            id_no = int(self.id_no.get())
            self.present = self.reg_file_details(id_no)
        except:
            pass
        if self.id_no.get() != "" and self.present is not None:
            self.table.delete(*self.table.get_children())
            His_manage = History_management()
            idno = int(self.id_no.get())
            His_manage.file_reader(idno)
            data_rows = ["Jan", "Feb", "Mar", "Apr", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            presence = [His_manage.month1_present, His_manage.month2_present, His_manage.month3_present,
                        His_manage.month4_present, His_manage.month5_present, His_manage.month6_present,
                        His_manage.month7_present, His_manage.month8_present, His_manage.month9_present,
                        His_manage.month10_present, His_manage.month11_present, His_manage.month12_present]
            absence = [His_manage.month1_absence, His_manage.month2_absence, His_manage.month3_absence,
                       His_manage.month4_absence, His_manage.month5_absence, His_manage.month6_absence,
                       His_manage.month7_absence, His_manage.month8_absence, His_manage.month9_absence,
                       His_manage.month10_absence, His_manage.month11_absence, His_manage.month12_absence]
            percentage = [His_manage.month1_percentage, His_manage.month2_percentage, His_manage.month3_percentage,
                          His_manage.month4_percentage, His_manage.month5_percentage, His_manage.month6_percentage,
                          His_manage.month7_percentage, His_manage.month8_percentage, His_manage.month9_percentage,
                          His_manage.month10_percentage, His_manage.month11_percentage, His_manage.month12_percentage]
            self.total_presence = 0
            self.total_absence = 0
            for i in range(0, 12):
                if presence[i] != None:
                    self.total_presence += presence[i]
                    self.total_absence += absence[i]
                self.table.insert('', index=END, values=([data_rows[i], presence[i], absence[i], percentage[i]]))
            year = int(datetime.today().strftime("%Y"))
            if year % 400 == 0 or year % 4 == 0 and year % 100 != 0:
                self.total_percentage = round(self.total_presence / 366 * 100, 2)
            else:
                self.total_percentage = round(self.total_presence / 365 * 100, 2)
            self.table.insert('', index=END,
                              values=(["Total", self.total_presence, self.total_absence, self.total_percentage]))

    def data_table(self):
        data_columns = ["Months","Presents","Absents","Percentage"]
        data_rows = ["Jan","Feb","Mar","Apr","May","June","Jul","Aug","Sep","Oct","Nov","Dec","Total"]
        self.table=ttk.Treeview(self,columns=data_columns,show="headings",height=13)
        """for i in range(0,13):
            self.table.insert("",index="end",values=(data_rows[i]))"""
        table_style = ttk.Style(self)
        table_style.configure("Treeview")
        table_style.configure("Treeview.Heading", font=("Arial black", 10))
        self.table.pack()
        self.table.heading('Months', text="MONTHS", anchor=tkinter.W)
        self.table.heading("Presents", text="PRESENTS", anchor=tkinter.W)
        self.table.heading('Absents', text="ABSENTS", anchor=tkinter.W)
        self.table.heading('Percentage', text="PERCENTAGE", anchor=tkinter.W)


    def search_bar(self):
        search_bar_frame = Frame(self,bg="#2e7e99")
        search_bar_frame.pack(pady=20)
        search_bar_name=Label(search_bar_frame,bg="#2e7e99",text="Enter ID.NO  ",font=("Arial Black",12),fg="white")
        search_bar_name.pack(side=LEFT)
        img = PhotoImage(file="Buttons/Search button.png")
        label = Label(image=img,width=20)
        label.img = img
        seach_button = Button(search_bar_frame,image=label.img,compound=CENTER,width=155,height=50,text="Show Record", font=("Arial black", 10), command=self.check_result,borderwidth=0,border=0, bg='#2e7e99',fg="white",activebackground="#2e7e99",activeforeground="#00ffff")
        seach_button.pack(side=RIGHT,padx=20)
        self.id_no=Entry(search_bar_frame, width=25, font=("Arial Black", 12),bg="#D8FCC9",background="white")
        self.id_no.pack(side=RIGHT)

    def record_name_list(self):
        self.name_list_box=Listbox(self,font=("Arial Black",10),width=40)
        self.name_list_box.pack()

    def take_registration(self):
        reg_list = []
        file = open("pathsfolder/address.data","rb")
        reg_file=pickle.load(file)
        work_file = openpyexcel.load_workbook(reg_file)
        sheet = work_file.worksheets[0]
        rows = sheet.max_row
        columns = sheet.max_column
        for r in range(2,rows+1):
            for c in range(1,columns+1):
                if c == 1:
                    self.reg_list.append(sheet.cell(r,c).value+"   "+str(sheet.cell(r,2).value))
                    reg_list=self.reg_list
        self.get_update(reg_list)

    def get_update(self,data):
        self.name_list_box.delete(0,END)
        for nameid in data:
            self.name_list_box.insert(END,nameid)

    def fill_entry(self,event):
        self.id_no.delete(0,END)
        name = self.name_list_box.get(ACTIVE)
        if name != "":
            name = name.split("   ")
            name = name[1]
            self.id_no.insert(0, name)

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

    def run_history(self):
        self.data_table()
        self.search_bar()
        self.record_name_list()
        self.take_registration()
        self.binding_key_list()

