## BALL PREDICTOR

App that forecast NBA results based on LSTM neural networks and XGBoost algorithm trained with data from 2003 to 2025.

### Structure

This repository is divided in 2 big modules. 
One is about the prediction of the matches. In this part, there is the data used, how it was collected, and the code behind the prediction. The neural network was trained using google collab.
The second module, is about the app code, the UI, and the interaction with the user.

### Execute app
In order to execute the app, execute the following command in the root directory you clone the repository to python -m uvicorn app.main:app --reload

