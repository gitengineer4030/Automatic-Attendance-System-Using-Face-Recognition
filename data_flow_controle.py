import pickle
from datetime import datetime
import openpyexcel
from openpyexcel.styles import numbers

class Data_Manager:
    def __init__(self):
        self.name = None
        self.father_name = None
        self.id_number = None
        self.subject = None
        self.phone_number = None
        self.present_name = None
        self.present_idnumber = None
        self.date = None
        self.time = None
        self.dateandtime = None
        self.All_data_list = []
        self.single_list = []
        self.single_value = []


    def saving_registration(self):
        file=open("pathsfolder/reg.data","wb")
        teacher_data=[self.name,self.father_name,self.id_number,self.subject,self.phone_number]
        pickle.dump(teacher_data,file)

    def store_registration(self):
        file = open("pathsfolder/reg.data", "rb")
        teacher_data=pickle.load(file)
        txtfile = open("pathsfolder/address3.data", "rb")
        reg_file=pickle.load(txtfile)
        workbook = openpyexcel.load_workbook(reg_file)
        sheet = workbook.worksheets[0]
        if workbook.active.title != "Registration":
            workbook.active.title = "Registration"
            workbook.save(reg_file)
        sheet.cell(1, 1).value = "NAME"
        sheet.cell(1, 2).value = "FATHER NAME"
        sheet.cell(1, 3).value = "ID.NO"
        sheet.cell(1, 4).value = "SUBJECT"
        sheet.cell(1, 5).value = "PHONE NUMBER"
        sheet.cell(1,6).value  = "Date of Registration"
        date=datetime.today().strftime("%d/%m/%Y")
        sheet.append([teacher_data[0].upper(),teacher_data[1].upper(),teacher_data[2],teacher_data[3].upper(),teacher_data[4],date])
        workbook.save(reg_file)
        #changing formate of cell
        row = sheet.max_row
        colums = sheet.max_column
        for r in range(1, row + 1):
            for c in range(1, colums + 1):
                if c == 3 or c == 5:
                    sheet.cell(r, c).number_format = numbers.FORMAT_NUMBER
                    workbook.save(reg_file)

    def registration_checking(self):
        txtfile = open("pathsfolder/address3.data", "rb")
        reg_file = pickle.load(txtfile)
        workbook = openpyexcel.load_workbook(reg_file)
        sheet = workbook.worksheets[0]
        row = sheet.max_row
        colums = sheet.max_column
        name_list = []
        id_list = []
        for r in range(2, row + 1):
            name_list.append(sheet.cell(r, 1).value.upper())
            id_list.append(sheet.cell(r, 3).value)
        self.present_idnumber = int(self.present_idnumber)
        if self.present_idnumber in id_list:
            index_of_id = id_list.index(self.present_idnumber)
            if self.present_name == name_list[index_of_id]:
                return self.present_idnumber
        elif self.present_idnumber not in id_list:
            return False

    def attendance_data(self):
        myfile = open("pathsfolder/address.data","rb")
        address = pickle.load(myfile)
        workbook = openpyexcel.load_workbook(address)
        #sheet1 = workbook.worksheets[0]
        sheet1 = self.sheets_setup(address,workbook)
        row = sheet1.max_row
        colums = sheet1.max_column
        if "Sheet" in workbook.sheetnames:
            sheet = workbook["Sheet"]
            workbook.remove(sheet)
            workbook.save(address)
        sheet1.cell(1, 1).value = "NAME"
        sheet1.cell(1, 2).value = "ID.NO"
        sheet1.cell(1, 3).value = "ATTENDANCE"
        sheet1.cell(1, 4).value = "DATE"
        sheet1.cell(1, 5).value = "TIME"

        id_no=self.registration_checking()
        if id_no == False:
            print("You are Not registed person but you are Known person")
        elif id_no !=False:
            for r in range(2, row + 1):
                for c in range(1, colums):
                    self.single_list.append(sheet1.cell(r,c).value)
                if self.single_list not in self.All_data_list:
                    self.All_data_list.append(self.single_list)
                    self.single_list = []
            single_value = [self.present_name, id_no, 'present', self.date]
            if single_value not in self.All_data_list:
                single_value.clear()
                sheet1.append([self.present_name, id_no, 'present', self.date, self.time])
                workbook.save(address)
                for r in range(1, row + 1):
                    for c in range(1, colums + 1):
                        if c == 2:
                            sheet1.cell(r, c).number_format = numbers.FORMAT_NUMBER
                            workbook.save(address)
                        elif c == 4:
                            sheet1.cell(r, c).number_format = numbers.FORMAT_DATE_XLSX22
                            workbook.save(address)

    def sheets_setup(self,address,workbook):
        month =datetime.today().month
        sheet = None
        if month == 1:
            if "Jan" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Jan", index=0)
                workbook.save(address)
            elif "Jan" in workbook.sheetnames:
                sheet = workbook["Jan"]
                workbook.save(address)
        elif month == 2:
            if "Feb" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Feb", index=1)
                workbook.save(address)
            elif "Feb" in workbook.sheetnames:
                sheet = workbook["Feb"]
                workbook.save(address)
        elif month == 3:
            if "Mar" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Mar", index=2)
                workbook.save(address)
            elif "Mar" in workbook.sheetnames:
                sheet = workbook["Mar"]
                workbook.save(address)
        elif month == 4:
            if "Apr" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Apr", index=3)
                workbook.save(address)
            elif "Apr" in workbook.sheetnames:
                sheet = workbook["Apr"]
                workbook.save(address)
        elif month == 5:
            if "May" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="May", index=4)
                workbook.save(address)
            elif "May" in workbook.sheetnames:
                sheet = workbook["May"]
                workbook.save(address)
        elif month == 6:
            if "June" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="June", index=5)
                workbook.save(address)
            elif "June" in workbook.sheetnames:
                sheet = workbook["June"]
                workbook.save(address)
        elif month == 7:
            if "Jul" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Jul", index=6)
                workbook.save(address)
            elif "Jul" in workbook.sheetnames:
                sheet = workbook["Jul"]
                workbook.save(address)
        elif month == 8:
            if "Aug" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Aug", index=7)
                workbook.save(address)
            elif "Aug" in workbook.sheetnames:
                sheet = workbook["Aug"]
                workbook.save(address)
        elif month == 9:
            if "Sep" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Sep", index=8)
                workbook.save(address)
            elif "Sep" in workbook.sheetnames:
                sheet = workbook["Sep"]
                workbook.save(address)
        elif month == 10:
            if "Oct" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Oct", index=9)
                workbook.save(address)
            elif "Oct" in workbook.sheetnames:
                sheet = workbook["Oct"]
                workbook.save(address)
        elif month == 11:
            if "Nov" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Nov", index=10)
                workbook.save(address)
            elif "Nov" in workbook.sheetnames:
                sheet = workbook["Nov"]
                workbook.save(address)
        elif month == 12:
            if "Dec" not in workbook.sheetnames:
                sheet = workbook.create_sheet(title="Dec", index=11)
                workbook.save(address)
            elif "Dec" in workbook.sheetnames:
                sheet = workbook["Dec"]
                workbook.save(address)
        return sheet