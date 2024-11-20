import os
import tempfile
from zairabase.utils.terminal import run_command

from . import T0_FILE, T1_FILE
from . import TAG
from . import MELLODDY_SUBFOLDER
from . import PARAMS_FILE, KEY_FILE
from . import NUM_CPU
from . import _SCRIPT_FILENAME


class AggregateActivity(object):
    def __init__(self, outdir):
        self.outdir = self.get_output_path(outdir)
        self.input_file_0 = self.get_input_file_0()
        self.input_file_1 = self.get_input_file_1()
        self.input_file_5 = self.get_input_file_5()

    def get_output_path(self, outdir):
        return os.path.join(outdir, MELLODDY_SUBFOLDER)

    def get_input_file_0(self):
        return os.path.join(self.outdir, T0_FILE)

    def get_input_file_1(self):
        return os.path.join(self.outdir, T1_FILE)

    def get_input_file_5(self):
        return os.path.join(self.outdir, TAG, "mapping_table", "T5.csv")

    def script_file(self):
        text = "tunercli agg_activity_data --assay_file {0} --activity_file {1} --mapping_table {2} --config_file {3} --key_file {4} --output_dir {5} --run_name {6} --number_cpu {7} --non_interactive".format(
            self.input_file_0,
            self.input_file_1,
            self.input_file_5,
            PARAMS_FILE,
            KEY_FILE,
            os.path.join(self.outdir),
            TAG,
            NUM_CPU,
        )
        tmp_dir = tempfile.mkdtemp()
        tmp_dir = "/home/mduranfrigola/Desktop/" #TODO this is hardcoded?
        self.script_path = os.path.join(tmp_dir, _SCRIPT_FILENAME)
        with open(self.script_path, "w") as f:
            f.write(text)

    def run(self):
        self.script_file()
        cmd = "bash {0}".format(self.script_path)
        run_command(cmd)
