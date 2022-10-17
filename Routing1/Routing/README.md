# Supply Chain - Cost/Route Optimization

### Overview:

- Route/Cost Optimization is mainly focused on minimizing/optimizing the overall cost invloved in transport of raw materials from suppliers to factories.
- Input: An excel file with information about materials, suppliers, factories etc. 
- output: A csv file with information about the quantity that needs to be shipped from each supplier.

### Technologies:
Below Technologies/Libraries has been used to develop this application.
- Python
- PULP
- Azure functions

- Note: For more details about the versions of the libaries used, refer "requirements.txt".

### Project Structure:
    ├── HttpTrigger1
    │   └── __init__.py -> contains the functionality to read and write data to the azure blob storage.
    │   └── helper_fun.py -> contains all the helper functions which are referred in init.py.
    │   └── preprocess.py -> contains all the functions to preprocess the data which are referred in init.py.    
    └── azure-pipelines.yml -> contains the deployment steps.
    └── requirements.txt -> contains all the required packages to run this application.

## To run this application locally:

- Clone the repository
- In a terminal, navigate to `SCM-Cost-optimization` folder
- Activate your desired virtual environment
- In the terminal, type `pip install -r requirements.txt`
- Run the application with `python __init__.py`

## Deployment:

- This web application has been deployed using azure pipelines.
- Under Pipelines => Create a new pipeline-> select Azure repos git -> Slect this repo (SCM-Cost-optimization) -> Select "Python Function App to Linux on Azure"
- Provide the authorization and select an already created function app from the dropdown.
- Yml file is generated -> save and run the pipeline.