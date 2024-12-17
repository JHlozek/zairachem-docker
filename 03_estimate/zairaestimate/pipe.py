import os
import json
import pandas as pd

from zairabase import ZairaBase
from zairabase.utils.pipeline import PipelineStep
from zairabase.vars import DATA_SUBFOLDER, DATA_FILENAME, PARAMETERS_FILE

from .from_classic.pipe import ClassicPipeline

from .from_fingerprint.pipe import FingerprintPipeline

from .from_individual_full_descriptors.pipe import IndividualFullDescriptorPipeline
"""
from .from_individual_full_descriptors_tabpfn.pipe import (
    IndividualFullDescriptorTabPFNPipeline,
)
from .from_manifolds.pipe import ManifoldPipeline
from .from_reference_embedding.pipe import ReferenceEmbeddingPipeline
from .from_ersilia_embedding.pipe import EosceEmbeddingPipeline
from .from_molmap.pipe import MolMapPipeline
from .evaluate import SimpleEvaluator
"""
MOLMAP_DATA_SIZE_LIMIT = 10000

class EstimatorPipeline(ZairaBase):
    def __init__(self, path):
        ZairaBase.__init__(self)
        if path is None:
            self.path = self.get_output_dir()
        else:
            self.path = path
        self.output_dir = os.path.abspath(self.path)
        assert os.path.exists(self.output_dir)
        self.params = self._load_params()
        self.get_estimators()
        self.data_size = self._get_data_size()

    def _get_data_size(self):
        data = pd.read_csv(
            os.path.join(self.get_trained_dir(), DATA_SUBFOLDER, DATA_FILENAME)
        )
        return data.shape[0]

    def _load_params(self):
        with open(os.path.join(self.path, DATA_SUBFOLDER, PARAMETERS_FILE), "r") as f:
            params = json.load(f)
        return params

    def get_estimators(self):
        self.logger.debug("Getting estimators")
        self._estimators_to_use = set()
        for x in self.params["estimators"]:
            self._estimators_to_use.update([x])

    def _classic_estimator_pipeline(self, time_budget_sec):
        if "baseline-classic" not in self._estimators_to_use:
            return
        step = PipelineStep("classic_estimator_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Running classic estimator pipeline")
            p = ClassicPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _fingerprint_estimator_pipeline(self, time_budget_sec):
        if "baseline-fingerprint" not in self._estimators_to_use:
            return
        step = PipelineStep("fingerprint_estimator_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Running fingerprint estimator pipeline")
            p = FingerprintPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _individual_estimator_pipeline(self, time_budget_sec):
        if "flaml-individual-descriptors" not in self._estimators_to_use:
            return
        step = PipelineStep("individual_estimator_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Running individual estimator pipeline")
            p = IndividualFullDescriptorPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _individual_estimator_tabpfn_pipeline(self, time_budget_sec):
        if "tabpfn-individual-descriptors" not in self._estimators_to_use:
            return
        step = PipelineStep("individual_estimator_pipeline_tabpfn", self.output_dir)
        if not step.is_done():
            self.logger.debug("Running individual estimator pipeline")
            p = IndividualFullDescriptorTabPFNPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _manifolds_pipeline(self, time_budget_sec):
        if "autogluon-manifolds" not in self._estimators_to_use:
            return
        step = PipelineStep("manifolds_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Running manifolds estimator pipeline")
            p = ManifoldPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _reference_pipeline(self, time_budget_sec):
        if "kerastuner-reference-embedding" not in self._estimators_to_use:
            return
        step = PipelineStep("reference_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Reference embedding pipeline")
            p = ReferenceEmbeddingPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _eosce_pipeline(self, time_budget_sec):
        step = PipelineStep("eosce_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Ersilia compound embedding pipeline")
            p = EosceEmbeddingPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _molmap_pipeline(self, time_budget_sec):
        if "molmap" not in self._estimators_to_use:
            return
        if self.data_size > MOLMAP_DATA_SIZE_LIMIT:
            self.logger.info("Data set is too big for molmap")
            return
        step = PipelineStep("molmap_pipeline", self.output_dir)
        if not step.is_done():
            self.logger.debug("Molmap estimator pipeline")
            p = MolMapPipeline(path=self.path)
            p.run(time_budget_sec=time_budget_sec)
            step.update()

    def _simple_evaluation(self):
        self.logger.debug("Simple evaluation")
        step = PipelineStep("simple_evaluation", self.output_dir)
        if not step.is_done():
            SimpleEvaluator(path=self.path).run()
            step.update()

    def run(self, time_budget_sec=None):
        self._classic_estimator_pipeline(time_budget_sec)
        self._fingerprint_estimator_pipeline(time_budget_sec)
        self._individual_estimator_tabpfn_pipeline(time_budget_sec)
        self._individual_estimator_pipeline(time_budget_sec)
        self._manifolds_pipeline(time_budget_sec)
        self._reference_pipeline(time_budget_sec)
        self._eosce_pipeline(time_budget_sec)
        self._molmap_pipeline(time_budget_sec)
        self._simple_evaluation()
