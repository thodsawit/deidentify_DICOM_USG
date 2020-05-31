"""
MDCU_ GI Endoscopy Center
v1-v5: Tepapap Apiparakoon (main contributor)
rev1: Thodsawit Tiyarattanachai

#######################################
v5_rev1:
Important Notes:
- To prevent data loss, please try on a small sample of images first.
- This code assumes that all DICOM files are ended with '.dcm'
- For consistency, special symbols including '-' and '/' are removed from HN and accession before they are being encoded.

Features of this code:
- remove 'burned-in' patient identifiers at the top of each USG image by changing 10%-top part of the image to be black banner
- DICOM metadata are either 'removed', 'encoded' or 'kept as it is'
    - 'removed' metadata includes the following:
        PatientName
        PresentationIntentType
        ReferringPhysicianName
        PatientBirthDate
        PatientBirthTime
        DeviceSerialNumber
        StationName
        InstitutionalDepartmentName
        OperatorsName
        RequestingPhysician
        RequestingService
        ReferencedSOPInstanceUID
        TransducerType
        PatientSex
        PatientAge
        SeriesDate
        ContentDate
        AcquisitionDateTime
        StudyTime
        SeriesTime
        ContentTime
        StudyID
        InstanceCreationDate
        InstanceCreationTime
        InstitutionName
        PerformedProcedureStepStartDate
        PerformedProcedureStepStartTime
        PerformedProcedureStepID
        PerformedProcedureStepDescription
    - 'encoded' metadata includes the following:
        *These identifiers are encoded by sha256 standard for the purpose of linking the images to annotations
        *Pairs of original identifier and encodings are written to a csv file, which will be kept at data owner's institution
        AccessionNumber
        PatientID
        StudyDate
        StudyInstanceUID
        InstanceUID
        SeriesInstanceUID
        SOPClassUID
    - Other metadata are 'kept as it is'. These metadata are useful for image processing, for example:
        location of ultrasound pane
        physical distance per pixel --> can be used to approximate real-world lesion size
        color channel system, e.g. RGB, GRAYSCALE, YBR
        ultrasound manufacturer and model name --> can be used for subgroup analysis and debiasing
- ancillary features: This program can also encode report and annotation files,
but those lines of codes were commented out at this stage. Let's try with only images first.

How to use this code:
- simply run the code in command line by parsing image directory, for example:
    python encode_dicom_V5_rev1.py --imgdir <image directory>
    if no image directory is specified, the program will browse through default 'images' folder located at the same level as python code
    i.e. you can copy images to the 'images' folder instead of parsing --imgdir argument
- The program will output two things to the 'dcm_mod' folder:
    - de-identified images will be in the subfolder 'DICOM_mod'
    - 'master_encode.csv' contains pairs of original identifiers and encodings.

Libraries required:
tqdm: 'conda install -c conda-forge tqdm' or 'pip install tqdm'
pydicom: 'conda install -c conda-forge pydicom' or 'pip install pydicom'
gdcm (need to install along with pydicom): 'conda install gdcm -c conda-forge'
#######################################
"""


from tqdm import tqdm
from PIL import Image
import pandas as pd
import numpy as np
import hashlib
import pydicom
import os
import argparse


def encrypt_string(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature



#Tue
#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--imgdir", default='images/', type=str,
                    help="directory containing DICOM images. Subdirectories are allowed.")
parser.add_argument("--reportdir", default='reports/', type=str,
                    help="directory containing reports. Subdirectories are allowed.")
args = parser.parse_args()




#Tue
image_path = args.imgdir
report_path = args.reportdir


if not os.path.isdir("dcm_mod"):
    os.mkdir("dcm_mod")
    os.mkdir("dcm_mod/DICOM_mod")


# Manage excel file containing annotations
"""
query_data = []     #for output excel file containing encoded patient data
found_excel = False
for root, dirs, files in os.walk(report_path):
    for filename in files:
        if filename.endswith(".xlsx") and not found_excel:
            excel_file_path = os.path.join(root,filename)
            query_df = pd.read_excel(excel_file_path)   #original patient data
            query_df['HN_encode'] = ""
            query_df['accession number_encode'] = ""
            for i in query_df.index:
                #Tue
                query_df['HN'][i] = str(query_df['HN'][i]).strip().replace('/', '').replace('-','')
                query_df['accession number'][i] = str(query_df['accession number'][i]).strip().replace('/', '').replace('-','')
                query_data.append((str(query_df['HN'][i]).strip(), str(query_df['study_date'][i]).strip(), str(query_df['accession number'][i]).strip()))
                query_df['HN_encode'][i] = encrypt_string(str(query_df['HN'][i]).strip())
                query_df['accession number_encode'][i] = encrypt_string(str(query_df['accession number'][i]).strip())
            # save original excel file (have both original and encode)
            original_writer = pd.ExcelWriter('dcm_mod/patients_review_original.xlsx', engine='xlsxwriter')
            query_df.to_excel(original_writer,index=False)
            # drop column
            query_df = query_df.drop(columns="HN")
            query_df = query_df.drop(columns="accession number")
            # save encode excel file (have only encode)
            encode_writer = pd.ExcelWriter("dcm_mod/patients_review_encode.xlsx", engine='xlsxwriter')
            query_df.to_excel(encode_writer,index=False)
            print("Finished query data from excel file")
            original_writer.save()
            encode_writer.save()
            query_found = True
            break
print("Total",str(len(query_data)),"cases")
"""


error_file = []
patient_details = {'PatientID':[], 'PatientID_encode':[], 'StudyDate':[], 'StudyDate_encode': [], 'AccessionNumber':[],'AccessionNumber_encode':[], 'StudyInstanceUID':[], 'StudyInstanceUID_encode':[], 'InstanceUID':[], 'InstanceUID_encode':[], 'SeriesInstanceUID':[], 'SeriesInstanceUID_encode':[], 'SOPClassUID':[], 'SOPClassUID_encode':[]}

with open('dcm_mod/master_encode.csv', 'w') as csvFile:
    for root, dirs, files in os.walk(image_path):
        #print(root, dirs, files)
        for my_file in tqdm(files):
            if my_file.endswith(".dcm"):
                #in_query = False
                filename = my_file.split("/")[-1]
                file_path = os.path.join(root,filename)

                try:
                    ds = pydicom.dcmread(file_path)
                    ds.decompress()
                    # read image data
                    img = ds.pixel_array
                    h = img.shape[0]
                    w = img.shape[1]
                    c = len(img.shape)
                    pad_space = int(0.1*h)
                    if c==2:
                        img[:pad_space,:] = np.zeros((pad_space,w))
                    elif c==3:
                        img[:pad_space,:,:] = np.zeros((pad_space,w,3))
                    ds.PixelData = img.tobytes()

                    # original data
                    AccessionNumber = ds.AccessionNumber.replace('-','').replace('/','')
                    PatientID = ds.PatientID.replace('-','').replace('/','')
                    #PatientName = str(ds.PatientName).replace("^"," ")
                    StudyInstanceUID = ds.StudyInstanceUID
                    StudyDate = ds.StudyDate
                    InstanceUID = ds.SOPInstanceUID
                    SeriesInstanceUID = ds.SeriesInstanceUID
                    SOPClassUID = ds.SOPClassUID

                    # get the data follow query_patients_HN
                    #if (str(PatientID).strip(),str(StudyDate).strip(),str(AccessionNumber).strip()) in query_data:
                    # in_query = True
                    #Tue
                    #query images regardless whether they are in query_data or not
                    AccessionNumber_encode = encrypt_string(AccessionNumber)
                    PatientID_encode = encrypt_string(PatientID)
                    #PatientName_encode = encrypt_string(PatientName)
                    StudyDate_encode = encrypt_string(StudyDate)    #Tue rev1
                    StudyInstanceUID_encode = encrypt_string(StudyInstanceUID)
                    InstanceUID_encode = encrypt_string(InstanceUID)
                    SeriesInstanceUID_encode = encrypt_string(SeriesInstanceUID)
                    SOPClassUID_encode = encrypt_string(SOPClassUID)

                    # Replace private metadata with encodings
                    ds.remove_private_tags()
                    ds.AccessionNumber = AccessionNumber_encode
                    ds.PatientID = PatientID_encode
                    #ds.PatientName = PatientName_encode
                    ds.StudyDate = StudyDate_encode     #Tue rev1
                    ds.StudyInstanceUID = StudyInstanceUID_encode
                    ds.SOPInstanceUID = InstanceUID_encode
                    ds.SeriesInstanceUID = SeriesInstanceUID_encode
                    ds.SOPClassUID = SOPClassUID_encode

                    #remove identifiers
                    ds.PatientName = '-'
                    #ds.ImageType = '-'
                    #ds.SOPClassUID = '-'
                    #ds.Modality = '-'
                    ds.PresentationIntentType = '-'
                    #ds.Manufacturer = '-'
                    ds.ReferringPhysicianName = '-'
                    ds.PatientBirthDate = '-'
                    ds.PatientBirthTime = '-'
                    #ds.StudyDescription = '-'
                    ds.DeviceSerialNumber = '-'
                    ds.StationName = '-'
                    ds.InstitutionalDepartmentName = '-'
                    ds.OperatorsName ='-'
                    ds.RequestingPhysician = '-'
                    ds.RequestingService = '-'
                    #ds.ManufacturerModelName = '-'
                    #ds.HeartRate = '-'
                    #ds.ProtacalName = '-'
                    #ds.TransducerData = '-'
                    #ds.ProcessingFunction = '-'
                    ds.ReferencedSOPInstanceUID = '-'
                    ds.TransducerType = '-'
                    ds.PatientSex = '-'
                    ds.PatientAge = '-'
                    #ds.StudyDate = '-'
                    ds.SeriesDate = '-'
                    ds.ContentDate = '-'
                    ds.AcquisitionDateTime = '-'
                    ds.StudyTime = '-'
                    ds.SeriesTime = '-'
                    ds.ContentTime = '-'
                    ds.StudyID = '-'
                    ds.InstanceCreationDate = '-'
                    ds.InstanceCreationTime = '-'
                    ds.InstitutionName = '-'
                    ds.PerformedProcedureStepStartDate = '-'
                    ds.PerformedProcedureStepStartTime = '-'
                    ds.PerformedProcedureStepID = '-'
                    ds.PerformedProcedureStepDescription = '-'

                    #write pairs of original identifiers and encodings to a csv file
                    patient_details['AccessionNumber'].append(AccessionNumber)
                    patient_details['AccessionNumber_encode'].append(AccessionNumber_encode)
                    patient_details['PatientID'].append(PatientID)
                    patient_details['PatientID_encode'].append(PatientID_encode)
                    #patient_details['PatientName'].append(PatientName)
                    patient_details['StudyDate'].append(StudyDate)
                    patient_details['StudyDate_encode'].append(StudyDate_encode)
                    patient_details['StudyInstanceUID'].append(StudyInstanceUID)
                    patient_details['StudyInstanceUID_encode'].append(StudyInstanceUID_encode)
                    patient_details['InstanceUID'].append(InstanceUID)
                    patient_details['InstanceUID_encode'].append(InstanceUID_encode)
                    patient_details['SeriesInstanceUID'].append(SeriesInstanceUID)
                    patient_details['SeriesInstanceUID_encode'].append(SeriesInstanceUID_encode)
                    #Tue
                    patient_details['SOPClassUID'].append(SOPClassUID)
                    patient_details['SOPClassUID_encode'].append(SOPClassUID_encode)

                    #create subdirectories
                    origin_subfolder = (root.replace(image_path,"").replace('\\', '/').strip())[1:].split('/')
                    encode_subfolder = ""
                    for subfol in origin_subfolder:
                        encode_subfolder += encrypt_string(subfol)+"/"
                    if not os.path.isdir("dcm_mod/DICOM_mod/"+encode_subfolder):
                        os.makedirs("dcm_mod/DICOM_mod/"+encode_subfolder)

                    ds.save_as("dcm_mod/DICOM_mod/"+encode_subfolder+InstanceUID_encode[:int(len(InstanceUID_encode)/2)]+".dcm")


                except:
                    print('Error: ', filename)
                    error_file.append(filename)


df = pd.DataFrame(patient_details, columns= ['PatientID', 'PatientID_encode', 'StudyDate', 'StudyDate_encode', 'AccessionNumber', 'AccessionNumber_encode', 'StudyInstanceUID', 'StudyInstanceUID_encode', 'InstanceUID', 'InstanceUID_encode', 'SeriesInstanceUID', 'SeriesInstanceUID_encode', 'SOPClassUID', 'SOPClassUID_encode'])
export_csv = df.to_csv(r'dcm_mod/master_encode.csv', index = None, header=True)


if len(error_file)>0:
    print("\nList of error files")
    for e in error_file:
        print(e)
else:
    print('No error file')
        