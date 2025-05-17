# indexer.py

import os
import copy
from kag.builder.component import KGWriter, RelationMapping, SPGTypeMapping
from kag.builder.component.scanner.json_scanner import JSONScanner
from kag.common.conf import KAG_CONFIG
from kag.common.registry import import_modules_from_path
from kag.interface import KAGBuilderChain as BuilderChainABC
from kag.builder.runner import BuilderChainRunner


def index_json():
    # 1. 注册自定义组件（JsonScanner、Mapping 等）
    import_modules_from_path(os.getcwd())
    pwd = os.path.dirname(__file__)
    # 2. 根据 config 实例化 Runner
    json_runner_config = KAG_CONFIG.all_config["json_runner"]
    for spg_type_name in ["FeatureValue","VisualFeature","IMUFeature","TimePoint","Relation","SpatioTemporalRelation","MotionSample"]:
        runner_config = copy.deepcopy(json_runner_config)
        runner_config["chain"]["mapping"]["spg_type_name"] = spg_type_name
        file_path = os.path.join(pwd, f"data/sub_data/{spg_type_name}.json")
        if not os.path.exists(file_path):
            continue
        runner = BuilderChainRunner.from_config(runner_config)
        runner.invoke(file_path)


if __name__ == "__main__":
    index_json()
