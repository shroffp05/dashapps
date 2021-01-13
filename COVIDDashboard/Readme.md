<h2> US Covid Data Tracker (2020) by State and County </h2> 

---

Dashboard tracks the number of covid cases over the Year 2020 in the United States by State and County. It also looks at Mask usage by state. 

The data is sourced from the New York Times, based on reports from state and local health agencies. More information about the data and the metrics can be found here: https://github.com/nytimes/covid-19-data

You can access the app here: https://covid-dashboard-20.herokuapp.com/

<h3> Getting Started </h3>

---

<h4> Running the app locally </h4> 

We suggest you to create a separate virtual environment running Python 3 for this app, and install all of the required dependencies there. Run in Terminal/Command Prompt:

```
git clone https://github.com/shroffp05/dashapps.git 
cd dashapps/COVIDDashboard 
python3 -m virtualenv venv
```

In UNIX system: 
```
source venv/bin/activate
```

In Windows:
```
venv\Scripts\activate 
```

To install all the required packages to this environment, simply run:
```
pip install -r requirements.txt 
```

and all the required pip packages will be installed, and the app will be able to run. 

To run the app: 
```
python app.py 
```

Dashboard:
![Alt text](/assets/COVID_Dashboard.PNG?raw=true)
