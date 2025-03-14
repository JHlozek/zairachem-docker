import os
import shutil
import json

from .files import ParametersFile, SingleFileForPrediction
from .standardize import ChemblStandardize
from .tasks import SingleTasksForPrediction
from .merge import DataMergerForPrediction
from .clean import SetupCleaner
from .check import SetupChecker

from zairabase import ZairaBase, create_session_symlink

from zairabase.vars import PARAMETERS_FILE
from zairabase.vars import RAW_INPUT_FILENAME
from zairabase.vars import DATA_SUBFOLDER
from zairabase.vars import DESCRIPTORS_SUBFOLDER
from zairabase.vars import ESTIMATORS_SUBFOLDER
from zairabase.vars import POOL_SUBFOLDER
from zairabase.vars import LITE_SUBFOLDER
from zairabase.vars import INTERPRETABILITY_SUBFOLDER
from zairabase.vars import APPLICABILITY_SUBFOLDER
from zairabase.vars import REPORT_SUBFOLDER
from zairabase.vars import OUTPUT_FILENAME

from zairabase.utils.pipeline import PipelineStep, SessionFile


class PredictSetup(object):
    def __init__(self, input_file, model_dir, output_dir, time_budget=120):
        self.input_file = os.path.abspath(input_file)
        if output_dir is None:
            self.output_dir = os.path.abspath(self.input_file.split(".")[0])
        else:
            self.output_dir = os.path.abspath(output_dir)
        #if os.path.exists(self.output_dir): # TODO add if wanted
            #shutil.rmtree(self.output_dir)
        assert model_dir is not None, "Model directory not specified"
        self.model_dir = os.path.abspath(model_dir)
        assert self.model_is_ready(), "Model is not ready"
        self.time_budget = time_budget  # TODO

    def model_is_ready(self):
        if not os.path.exists(self.model_dir):
            return False
        if not os.path.exists(os.path.join(self.model_dir, OUTPUT_FILENAME)):
            return False
        if not os.path.exists(os.path.join(self.model_dir, ESTIMATORS_SUBFOLDER)):
            return False
        return True

    def _copy_input_file(self):
        extension = self.input_file.split(".")[-1]
        shutil.copy(
            self.input_file,
            os.path.join(self.output_dir, RAW_INPUT_FILENAME + "." + extension),
        )

    def _make_output_dir(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

    def _open_session(self):
        sf = SessionFile(self.output_dir)
        sf.open_session(
            mode="predict", output_dir=self.output_dir, model_dir=self.model_dir
        )
        create_session_symlink(self.output_dir)

    def _make_subfolder(self, name):
        os.makedirs(os.path.join(self.output_dir, name))

    def _make_subfolders(self):
        self._make_subfolder(DATA_SUBFOLDER)
        self._make_subfolder(DESCRIPTORS_SUBFOLDER)
        self._make_subfolder(ESTIMATORS_SUBFOLDER)
        self._make_subfolder(POOL_SUBFOLDER)
        self._make_subfolder(LITE_SUBFOLDER)
        self._make_subfolder(INTERPRETABILITY_SUBFOLDER)
        self._make_subfolder(APPLICABILITY_SUBFOLDER)
        self._make_subfolder(REPORT_SUBFOLDER)
        shutil.copyfile(
            os.path.join(self.model_dir, DATA_SUBFOLDER, PARAMETERS_FILE),
            os.path.join(self.output_dir, DATA_SUBFOLDER, PARAMETERS_FILE),
        )
    
    def _initialize(self):
        step = PipelineStep("initialize", self.output_dir)
        if not step.is_done():
            self._make_output_dir()
            self._make_subfolders()
            self._open_session()
            self._copy_input_file()
            step.update()

    def _normalize_input(self):
        step = PipelineStep("normalize_input", self.output_dir)
        if not step.is_done():
            params = ParametersFile(
                full_path=os.path.join(self.model_dir, DATA_SUBFOLDER, PARAMETERS_FILE)
            ).load()
            f = SingleFileForPrediction(self.input_file, params)
            f.process()
            self.has_tasks = f.has_tasks
            step.update()

    def _standardize(self):
        step = PipelineStep("standardize", self.output_dir)
        if not step.is_done():
            std = ChemblStandardize(os.path.join(self.output_dir, DATA_SUBFOLDER))
            std.run()
            step.update()

    def _tasks(self):
        step = PipelineStep("tasks", self.output_dir)
        if not step.is_done():
            SingleTasksForPrediction(
                os.path.join(self.output_dir, DATA_SUBFOLDER)
            ).run()
            step.update()

    def _merge(self):
        step = PipelineStep("merge", self.output_dir)
        if not step.is_done():
            DataMergerForPrediction(os.path.join(self.output_dir, DATA_SUBFOLDER)).run(
                self.has_tasks
            )
            step.update()

    def _clean(self):
        step = PipelineStep("clean", self.output_dir)
        if not step.is_done():
            SetupCleaner(os.path.join(self.output_dir, DATA_SUBFOLDER)).run()
            step.update()

    def _check(self):
        step = PipelineStep("setup_check", self.output_dir)
        if not step.is_done():
            SetupChecker(self.output_dir).run()
            step.update()

    def update_elapsed_time(self):
        ZairaBase().update_elapsed_time()

    def is_done(self):
        if os.path.exists(os.path.join(self.output_dir, OUTPUT_FILENAME)):
            return True
        else:
            return False

    def setup(self):
        self._initialize()
        self._normalize_input()
        self._standardize()
        if self.has_tasks:
            self._tasks()
        self._merge()
        self._check()
        self._clean()
        self.update_elapsed_time()

class ONNXPredictSetup(PredictSetup):
    def __init__(self, input_file, output_dir, model_dir, time_budget):
        super().__init__(input_file, output_dir, model_dir, time_budget)
            
    def _make_subfolders(self):
        self._make_subfolder(DATA_SUBFOLDER)
        self._make_subfolder(INTERPRETABILITY_SUBFOLDER)
        self._make_subfolder(APPLICABILITY_SUBFOLDER)
        self._make_subfolder(REPORT_SUBFOLDER)
        
    def _normalize_input(self):
        step = PipelineStep("normalize_input", self.output_dir)
        if not step.is_done():
            f = SingleFileForPrediction(self.input_file, None)
            f.process()
            self.has_tasks = f.has_tasks
            step.update()
        
    def setup(self):
        self._initialize()
        self._normalize_input()
        self._standardize()
        if self.has_tasks:
            self._tasks()
        self._merge()
        self._clean()
        self.update_elapsed_time()


