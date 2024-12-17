import os
import pandas as pd
import json
import numpy as np

from zairabase import ZairaBase
from zairabase.vars import (
    INPUT_SCHEMA_FILENAME,
    MAPPING_FILENAME,
    COMPOUND_IDENTIFIER_COLUMN,
    PARAMETERS_FILE,
    SMILES_COLUMN,
    DATA_SUBFOLDER, 
    DATA_FILENAME
)


class BaseEstimator(ZairaBase):
    def __init__(self, path):
        ZairaBase.__init__(self)
        if path is None:
            self.path = self.get_output_dir()
        else:
            self.path = path
        self.logger.debug(self.path)
        if self.is_predict():
            self.trained_path = self.get_trained_dir()
        else:
            self.trained_path = self.path
        self.task = self._get_task()
    
    def get_Y_col(self):
        if self.task == "classification":
            Y_col = "bin"
        if self.task == "regression":
            Y_col = "reg"
        return Y_col

    def _get_total_time_budget_sec(self):
        with open(os.path.join(self.path, DATA_SUBFOLDER, PARAMETERS_FILE), "r") as f:
            time_budget = json.load(f)["time_budget"]
        return int(time_budget) * 60 + 1
    
    def _get_task(self):
        with open(os.path.join(self.path, DATA_SUBFOLDER, PARAMETERS_FILE), "r") as f:
            task = json.load(f)["task"]
        return task
    
    def _estimate_time_budget(self):
        elapsed_time = self.get_elapsed_time()
        print("Elapsed time: {0}".format(elapsed_time))
        total_time_budget = self._get_total_time_budget_sec()
        print("Total time budget: {0}".format(total_time_budget))
        available_time = total_time_budget - elapsed_time
        # Assuming classification and regression will be done
        available_time = available_time / 2.0
        # Substract retraining and subsequent tasks
        available_time = available_time * 0.8
        available_time = int(available_time) + 1
        print("Available time: {0}".format(available_time))
        return available_time


class BaseOutcomeAssembler(ZairaBase):
    def __init__(self, path=None):
        ZairaBase.__init__(self)
        if path is None:
            self.path = self.get_output_dir()
        else:
            self.path = path
        if self.is_predict():
            self.trained_path = self.get_trained_dir()
        else:
            self.trained_path = self.path

    def _get_mappings(self):
        return pd.read_csv(os.path.join(self.path, DATA_SUBFOLDER, MAPPING_FILENAME))

    def _get_compounds(self):
        return pd.read_csv(os.path.join(self.path, DATA_SUBFOLDER, DATA_FILENAME))[
            [COMPOUND_IDENTIFIER_COLUMN, SMILES_COLUMN]
        ]

    def _get_original_input_size(self):
        with open(
            os.path.join(self.path, DATA_SUBFOLDER, INPUT_SCHEMA_FILENAME), "r"
        ) as f:
            schema = json.load(f)
        file_name = schema["input_file"]
        return pd.read_csv(file_name).shape[0]

    def _remap(self, df, mappings):
        n = self._get_original_input_size()
        ncol = df.shape[1]
        R = [[None] * ncol for _ in range(n)]
        for m in mappings.values:
            i, j = m[0], m[1]
            if np.isnan(j):
                continue
            R[i] = list(df.iloc[int(j)])
        return pd.DataFrame(R, columns=list(df.columns))
