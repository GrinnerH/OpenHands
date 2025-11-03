#!/usr/bin/env python3
import asyncio
import json
import sys
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.setup import create_runtime
from openhands.events.action import NullAction
import tempfile

async def replay_from_jsonl(jsonl_file: str, instance_id: str):
    """直接从 output.jsonl 回放，无需提取"""

    # 1. 找到并提取 history
    history = None
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            if data['instance_id'] == instance_id:
                history = data['history']
                break

    if not history:
        print(f"未找到实例: {instance_id}")
        return

    # 2. 临时保存为标准格式
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(history, f)
        temp_path = f.name

    # 3. 回放
    config = AppConfig(
        default_agent='CodeActAgent',
        replay_trajectory_path=temp_path,
    )

    runtime = create_runtime(config)
    await runtime.connect()

    try:
        state = await run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )
        print(f"回放完成: {state.agent_state}")
    finally:
        runtime.close()

if __name__ == '__main__':
    asyncio.run(replay_from_jsonl(sys.argv[1], sys.argv[2]))