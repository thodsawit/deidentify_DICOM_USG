# deidentify_DICOM_USG
de-identify patient information from DICOM ultrasound images

### Important Notes
- This code assumes that all DICOM files are ended with '.dcm'
- For consistency, special symbols including '-' and '/' are removed from HN and accession before they are being encoded.

### Features of this code
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
        StudyID
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

### How to use this code
- simply run the code in command line by parsing image directory, for example:
    python encode_dicom_V5_rev1.py --imgdir <image directory>
    if no image directory is specified, the program will browse through default 'images' folder located at the same level as python code
    i.e. you can copy images to the 'images' folder instead of parsing --imgdir argument
- The program will output two things to the 'dcm_mod' folder:
    - de-identified images will be in the subfolder 'DICOM_mod'
    - 'master_encode.csv' contains pairs of original identifiers and encodings.

### Libraries required
- tqdm: 'conda install -c conda-forge tqdm' or 'pip install tqdm'
- pydicom: 'conda install -c conda-forge pydicom' or 'pip install pydicom'
- gdcm (need to install along with pydicom): 'conda install gdcm -c conda-forge'

