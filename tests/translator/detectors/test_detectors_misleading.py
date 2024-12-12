# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
import pytest
import re
import types

import garak
from garak import _plugins
from garak.attempt import Attempt
from garak.configurable import Configurable
from garak.detectors.misleading import MustContradictNLI
from garak.detectors.base import HFDetector
import pytest
from garak.attempt import Attempt
from garak import _config
import importlib
from garak.harnesses.base import Harness
import os


@pytest.fixture
def hf_detector():
    local_config_path = str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    _config.run.translation["translation_service"] = 'local'
    _config.run.translation["lang_spec"] = "ja"
    _config.run.translation["model_spec"]["model_name"] = "facebook/m2m100_418M"
    _config.run.translation["model_spec"]["tokenizer_name"] = "facebook/m2m100_418M"
    HFDetector.detector_model_path = "garak-llm/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli"
    HFDetector.detector_target_class = "label"
    HFDetector.tokenizer_kwargs = {"truncation": True, "max_length": 256}
    detector = HFDetector(_config)
    return detector 


@pytest.fixture
def must_contradict_NLI_detector():
    local_config_path = str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    _config.run.translation["translation_service"] = 'local'
    _config.run.translation["lang_spec"] = "ja"
    _config.run.translation["model_spec"]["model_name"] = "facebook/m2m100_418M"
    _config.run.translation["model_spec"]["tokenizer_name"] = "facebook/m2m100_418M"
    detector = MustContradictNLI(_config)
    return detector 


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_must_contradict_NLI_detection(must_contradict_NLI_detector):
    attempt = Attempt(prompt="これはテストプロンプトです")
    attempt.outputs = [
        "こんにちは world",
        "陰府 の 端 に は 陰府 の 穴 が あ る."
    ]

    results = must_contradict_NLI_detector.detect(attempt)
    assert results[0] < 0.1, "Detection results do not match expected values"
    assert results[1] < 0.5, "Detection results do not match expected values"
    importlib.reload(garak._config)
    garak._config.load_base_config()


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_hf_detector_detection(hf_detector):
    # Create a sample Attempt with Japanese text
    attempt = Attempt(prompt="2人の女性が持ち帰り用の荷物を持ちながら抱き合っている")
    attempt.outputs = ["男たちがデリカテッセンの外で喧嘩している"]

    # Run the detection
    results = hf_detector.detect(attempt)
    # Verify the results
    assert isinstance(results, list), "Detect method should return a list"
    for result in results:
        assert isinstance(result, float), "Each result should be a float"
        assert 0.0 <= result <= 1.0, "Each result should be between 0.0 and 1.0"
    importlib.reload(garak._config)
    garak._config.load_base_config()