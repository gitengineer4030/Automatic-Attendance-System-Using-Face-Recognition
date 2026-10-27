import pickle
import cv2
import os
import face_recognition
from datetime import datetime
import numpy
import data_flow_controle
import tkinter as tk
from tkinter import messagebox
###########################################################################################
class Attendance_taker():
    def __int__(self):
        self.images = []
        self.person_name = []
        self.encoding_List= []
        self.encoding_list= []
        self.name = None
        self.dateandtime = None
        self.cap = None
        self.name_list = []
################################################################################
    def image_and_person_name_path_provider(self):
        images = []
        person_name = []
        path = "Images"
        myList = os.listdir(path)
        if len(myList)==0:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("info","Before starting attendance,you have to register at least one person!")
            return False
        if len(myList)>0:
            for image_name in myList:
                images.append(f"{path}/{image_name}")
                person_name.append(os.path.splitext(image_name)[0])

        self.images = images
        self.person_name = person_name

    def face_encode_finder(self, img, name):
        encoding_list = []
        images = img
        person_name = name
        for image in images:
            print(images)
            single_image = cv2.imread(image)
            single_image = cv2.cvtColor(single_image, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(single_image)[0]
            encoding_list.append(encode)
        self.encoding_list = encoding_list
        for name, encode in zip(person_name, self.encoding_list):
            print(f'{name}', encode)
            numpy.save(f"Encodes/{name}", encode)

    def face_encode_check_refinder(self):
        persons_name = []
        pictures = os.listdir("Images\\")
        encoding_folder = os.listdir("Encodes\\")
        encode_adding_list = []
        for pic_encode in pictures:
            pic_encode = os.path.splitext(pic_encode)[0]
            pic_encode += '.npy'
            if pic_encode not in encoding_folder:
                pic_encode = os.path.splitext(pic_encode)[0]
                persons_name.append(pic_encode)
                encode_adding_list.append(f"Images/{pic_encode}.jpg")

        if len(encode_adding_list) > 0:
            print(f"{len(encode_adding_list)} pictures are found without existing its encode")
            self.face_encode_finder(encode_adding_list, persons_name)
        if len(encode_adding_list) == 0:
            print("Encoding is allready exist!")

    def load_store_encodings(self):
        encoding_list = []
        myfile=os.listdir(f"Encodes/")
        for file in myfile:
            encoding_list.append(numpy.load(f"Encodes/{file}"))
        self.encoding_list = encoding_list

    def myface_recognition(self):
        name_list = []
        id_list = []
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 120)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'M', 'J', 'P', 'G'))
        while True:
          cap = self.cap
          capturing,frame  =  cap.read()
          if capturing == False:
              break
          frame = cv2.flip(frame,1)
          edit_frame = cv2.resize(frame,(0,0),None,0.25,0.25)
          edit_frame = cv2.cvtColor(edit_frame,cv2.COLOR_BGR2RGB)
          faces_in_Frame=face_recognition.face_locations(edit_frame)
          encoding_of_face = face_recognition.face_encodings(edit_frame,faces_in_Frame)
          for encodeFace , faceLoc in zip(encoding_of_face,faces_in_Frame):
              matches=face_recognition.compare_faces(self.encoding_list,encodeFace)
              faceDis = face_recognition.face_distance(self.encoding_list,encodeFace)
              faceDis=faceDis.round(1)
              print(matches)
              matchIndex=numpy.argmin(faceDis)
              if matches[matchIndex] == True  and faceDis[matchIndex] <= 0.3:
                  name = self.person_name[matchIndex].upper()
                  ###############################
                  split_name = name.split(" ")
                  len_total_name = len(split_name)-1
                  nameid = split_name[len_total_name]
                  split_name_len = len(split_name) - 1
                  split_name = split_name[split_name_len]
                  real_name = name.split(split_name)
                  real_name = real_name[0]
                  name = real_name.strip()
                  if nameid not in id_list:
                      Data_Manager = data_flow_controle.Data_Manager()
                      id_list.append(nameid)
                      name_list.append(name)
                      date = datetime.today().strftime('%m/%d/%Y')
                      time = datetime.today().strftime('%I:%M')
                      Data_Manager.date = date
                      Data_Manager.time = time
                      Data_Manager.present_idnumber = nameid
                      Data_Manager.present_name = name
                      Data_Manager.attendance_data()
                  y1, x2, y2, x1 = faceLoc
                  y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                  cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                  cv2.putText(frame,name,(x1+25,y2+25),cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),1)
              else:
                  y1, x2, y2, x1 = faceLoc
                  y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                  cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                  cv2.putText(frame,'Unknown',(x1+25,y2+25),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)

          cv2.imshow("camera",frame)
          if cv2.waitKey(10) == 13:
              pass
        cap.release()
        cv2.destroyAllWindows()

    def date_time_saver(self):
        date = datetime.today().strftime('%m/%d/%Y')
        time = datetime.today().strftime('%I:%M')
        file = open("pathsfolder/date.data","wb")
        pickle.dump(date,file)

    def came_scanner(self):
        self.image_and_person_name_path_provider()
        self.face_encode_check_refinder()
        self.load_store_encodings()
        self.myface_recognition()
###########################################################################################################
##########################################################################################################
if __name__ == '__main__':
    Attendance_taker = Attendance_taker()
    Attendance_taker.image_and_person_name_path_provider()
    Attendance_taker.face_encode_check_refinder()
    Attendance_taker.load_store_encodings()
    Attendance_taker.myface_recognition()