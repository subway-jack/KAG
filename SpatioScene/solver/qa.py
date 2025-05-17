#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import logging

from kag.common.conf import KAG_CONFIG
from kag.common.registry import import_modules_from_path
from kag.interface import SolverPipelineABC

# Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

class SpatioSceneQA:
    """
    A lightweight Q&A client that reuses the same pipeline and omits the TraceLogReporter for reduced overhead.
    """
    def __init__(self, pipeline: SolverPipelineABC):
        self.pipeline = pipeline

    async def qa(self, query: str) -> str:
        """
        Invoke the pipeline asynchronously on the given query.
        """
        return await self.pipeline.ainvoke(query)

async def batch_run(questions):
    # 1) Pre-load custom modules and prompts
    import_modules_from_path(os.getcwd())
    import_modules_from_path("./prompt")

    # 2) Initialize and reuse a single SolverPipeline instance
    pipeline = SolverPipelineABC.from_config(
        KAG_CONFIG.all_config["solver_pipeline"]
    )
    qa_client = SpatioSceneQA(pipeline)

    # 3) Launch all Q&A tasks concurrently
    tasks = [qa_client.qa(q) for q in questions]
    answers = await asyncio.gather(*tasks, return_exceptions=True)

    # 4) Print results
    for q, ans in zip(questions, answers):
        if isinstance(ans, Exception):
            logger.error(f"Query [{q}] failed: {ans}")
        else:
            print(f"Question: {q}\n→ Answer: {ans}\n")

if __name__ == "__main__":
    # Example questions
    questions = [
        "What are the height (h) and position (x, y) of MotionSample(id=1622559600.0)?",
        "Which MotionSample has classId = 5, and what is its timestamp?",
        "For MotionSample(id=1622559625.3), what are the values of relationE, relationD, relationC, relationA, and relationB?",
        "Please list all visual feature values of MotionSample(id=1622559615.8).",
        "What is the third-dimension value of the imuVec feature in MotionSample(id=1622559645.9)?",
    ]
    asyncio.run(batch_run(questions))