# %% 
# Import external packages

from asyncio.log import logger
import pandas as pd
import neurokit2 as nk
import json
import logging
import matplotlib
from matplotlib import pyplot as plt
import numpy as np

#%%
#Logging
logger_subject = logging.getLogger('subjectlogger')
logger_termination = logging.getLogger('terminationlogger')

logging.basicConfig(filename='Subject.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')
# %%
# Definition of Classes

## Class Test
class Subject():
    """
    Test-Subject with the following attributes:

    - birth_year: int
    - age: int
    - subject_max_hr: int
    - subject_id: int
    - test_power_w: int

    """

    def __init__(self, file_name):
        """
        Initialize the Subject-Object with the following attributes:	
        - birth_year: int
        - age: int
        - subject_max_hr: int
        - subject_id: int
        - test_power_w: int
        - also log who reads every data with time and saves every manual terminated test with time
    
        """
        __f = open(file_name)
        __subject_data = json.load(__f)
        self.subject_id = __subject_data["subject_id"]
        self.birth_year = __subject_data["birth_year"]        
        self.age = 2022 - self.birth_year
        self.subject_max_hr = 220 - (2022 - __subject_data["birth_year"])
        self.test_power_w = __subject_data["test_power_w"]

        logger_subject.info('Data of Subject {} has been loaded.'.format(self.subject_id))

class PowerData():
    """
    Power data with the following attributes:
        
    - subject_id: int
    - powder_data_watts: array of int
    - duration: int
    """

    def __init__(self, file_name):
        """
        Initialize the PowerData-Object with the following attributes:
        - subject_id: int
        - powder_data_watts: array of int
        - duration: int
        """
        self.subject_id = file_name.split(".")[0][-1]
        self.power_data_watts = open(file_name).read().split("\n")
        self.power_data_watts.pop(-1)
        self.duration_s = len(self.power_data_watts)
        
class Test:
    """
    Perfomance test of a subject with the following attributes:
    - subject_id: int
    - ecg_data: pandas dataframe
    - manual_termination: bool
    - terminated: bool
    - maximum_hr: int
    - average_hr_test: int
    - duration_test_min: int
    - number_of_heartbeats: int


    """
    def __init__(self, file_name):
        """
        Initialize the Test-Object with the following attributes:
        - subject_id: int
        - ecg_data: pandas dataframe
        - manual_termination: bool
        """
        self.subject_id = file_name.split(".")[0][-1]
        self.ecg_data = pd.read_csv(file_name)
        self.manual_termination = False

    def create_hr_data(self):
        """
        Load a dataframe of ecg_data to add additional attributes to the test object

        """

        self.ecg_data["ECG"] = self.ecg_data.iloc[:, [1]]

        # Find peaks
        self.hr_peaks, self.info = nk.ecg_peaks(self.ecg_data["ECG"], sampling_rate=1000)

        self.number_of_heartbeats = self.hr_peaks["ECG_R_Peaks"].sum()

        self.duration_test_min = self.hr_peaks.size/1000/60

        self.average_hr_test = self.number_of_heartbeats / self.duration_test_min

        ## Calculate heart rate moving average

        self.hr_peaks['average_HR_10s'] = self.hr_peaks.rolling(window=10000).mean()*60*1000
        
        self.maximum_hr = self.hr_peaks['average_HR_10s'].max()

        #self.peaks['average_HR_10s'].plot()

        ## Calculate heart rate variability (natural time between two heartbeats, short HRV)

        self.heart_rate_variability = self.duration_test_min*60 / self.number_of_heartbeats

    def evaluate_termination(self):
        """
        Evaluate the automatic termination of the test
        """
        self.terminated = False
        if self.maximum_hr > self.subject.subject_max_hr:
            self.terminated = True
        return self.terminated

    def add_subject(self, Subject):
        """
        Add a subject to the test object
        """
        self.subject = Subject

    def add_power_data(self, PowerData):
        """
        Add a power data to the test object
        """
        self.power_data = PowerData

    def create_summary(self):
        """
        create a summary of the test and print it to the console
        """
        print("Summary for Subject " + str(self.subject.subject_id))
        print("Year of birth:  " + str(self.subject.birth_year))
        print("Test level power in W:  " + str(self.subject.test_power_w))
        print("Maximum HR was: " + str(self.maximum_hr))
        print("Average HR was: " + str(round(self.average_hr_test, 0)))
        print("Average HRV was: " +str(round(self.heart_rate_variability, 2)), "seconds")
        print("Was test terminated because exceeding HR: " + str(self.terminated))
        print("Was test terminated because for other reasons: " + str(self.manual_termination))

        print("________________")
        print(" \n")

    def ask_for_termination(self):
        """
        Ask the diagnostician if the test should be terminated
        """
        self.manual_termination = ""
        self.manual_termination = input("Is this test invalid? (leave blank if valid): ")

        if self.manual_termination != "":
            logger_termination.info('Test (Subject {}) has been terminated manually.' .format(self.subject_id))
            self.termination = True

    def path_plot(self):
        
        working_dir = os.path.dirname(file)
        destination_dir = os.path.join(working_dir, 'result_data')
        file_name = f"Subject {str(self.subject_id)} plot.jpeg"
        file_path = os.path.join(destination_dir, file_name)
        return file_path

    def create_plot(self):
        """
        Create a plot of the test
        """

        self.plot_data = pd.DataFrame()
        self.plot_data["Heart Rate"] = self.hr_peaks[self.ecg_data.index % 1000 == 0]["average_HR_10s"]  
        self.plot_data = self.plot_data.reset_index(drop=True)
        self.plot_data["Power (Watt)"] = pd.to_numeric(self.power_data.power_data_watts)


        fig = plt.figure()
        plt.subplot()
        plt.plot(self.plot_data["Heart Rate"], color="#420420", label = "Heart Rate")
        plt.title('Subject {}'.format(self.subject_id))
        ax = plt.subplot()
        plt.plot(self.plot_data["Power (Watt)"], color="#ffd966", label = "Power Watt")
        plt.tick_params(right=True, labelright=True )
        plt.xlabel('Zeit / Sekunden')
        plt.ylabel('Leistung / Watt')
        ax2 = ax.twinx()
        ax2.set_ylim(60,200)
        ax2.set_ylabel("Herzfrequenz / bpm")
        plt.legend(loc="lower right")
        plt.savefig(self.path_plot())
        plt.show()

    def save_data(self):
        """
        Store the test data in a JSON file
        """
        __data = {
            "Test": {
                    "User ID": self.subject_id,
                    "Automatic termination": self.terminated,
                    "Manual termination": self.manual_termination, 
                    "Average Heart Rate": self.average_hr_test,
                    "Heart rate variability": self.heart_rate_variability, 
                    "Maximum Heart Rate": self.maximum_hr, 
                    "Test Length (s)": self.power_data.duration_s, 
                    "Test Power (W)": self.subject.test_power_w,
                    "path of plot": self.path_plot()}
                    }

        __folder_current = os.path.dirname(__file__) 
        __folder_input_data = os.path.join(__folder_current, 'result_data')
        
        __file_name = 'result_data_subject' + str(self.subject_id) +'.json'
        __results_file = os.path.join(__folder_input_data, __file_name)

        with open(__results_file, 'w', encoding='utf-8') as f:
            json.dump(__data, f, ensure_ascii=False, indent=4)

# %% Eigentlich Ablauf der Event-Pipeline

## Einlesen der Daten

### Erstellen leerer Liste zur Verarbeitung
list_of_new_tests = []
list_of_subjects = []
list_of_power_data = []

### Füllen der Liste mit vorhandenen Daten

import os
from re import I
import pandas as pd

folder_current = os.path.dirname(__file__) 
folder_input_data = os.path.join(folder_current, 'input_data')
for file in os.listdir(folder_input_data):
    file_name = os.path.join(folder_input_data, file)

    if file.endswith(".csv"):
        list_of_new_tests.append(Test(file_name))

    if file.endswith(".json"):
        list_of_subjects.append(Subject(file_name))

    if file.endswith(".txt"):
        list_of_power_data.append(PowerData(file_name))


# %%
## Programmablauf

iterator = 0                                        # Zähler, der die gefundenen Dateien und damit Tests zählt

for test in list_of_new_tests:                      # Alle Tests werden nacheinander durchlaufen
    test.create_hr_data()                           # Erstelle Herzraten aus den EKG-Daten
    test.add_subject(list_of_subjects[iterator])    # Fügt einem Test die passenden Versuchspersonen hinzu
    test.evaluate_termination()                     # Prüft Abbruchskriterien
    test.add_power_data(list_of_power_data[iterator]) # Fügt power_data hinzu
    test.path_plot()                                #Path of plot
    test.create_plot()                              # Visualisierung der Leistunngsdaten
    test.create_summary()                           # Zusammenfassung der Leistungsdaten
    test.ask_for_termination()                      # Frage nach Abbruch
    test.save_data()                                # Speicher der Daten

    iterator = iterator + 1
 


# %%
