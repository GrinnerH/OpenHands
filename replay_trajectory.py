#!/usr/bin/env python3
"""
直接回放轨迹的脚本
用法: poetry run python replay_trajectory.py <trajectory_file>
"""

import asyncio
import sys
from pathlib import Path

from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.setup import create_runtime
from openhands.events.action import NullAction


async def replay(trajectory_file: str):
    """回放轨迹"""

    trajectory_path = Path(trajectory_file).resolve()

    if not trajectory_path.exists():
        print(f"❌ 轨迹文件不存在: {trajectory_path}")
        return

    print(f"🎬 开始回放轨迹")
    print(f"   文件: {trajectory_path}")
    print()

    # 创建配置（直接在代码中设置，不使用 TOML）
    config = AppConfig(
        default_agent='CodeActAgent',
        run_as_openhands=False,
        workspace_base=None,
        workspace_mount_path=None,
        max_iterations=100,
        replay_trajectory_path=str(trajectory_path),  # 关键：设置回放路径
    )

    print("📋 配置信息:")
    print(f"   Agent: {config.default_agent}")
    print(f"   最大迭代: {config.max_iterations}")
    print(f"   回放路径: {config.replay_trajectory_path}")
    print()

    # 创建 runtime
    print("🔧 创建运行时环境...")
    runtime = create_runtime(config)
    await runtime.connect()
    print("✓ 运行时已连接\n")

    try:
        # 运行回放（使用 NullAction 因为任务从轨迹中读取）
        print("▶️  开始回放...\n")
        print("=" * 80)

        state = await run_controller(
            config=config,
            initial_user_action=NullAction(),
            runtime=runtime,
        )

        print("=" * 80)
        print(f"\n✓ 回放完成!")
        print(f"   最终状态: {state.agent_state}")
        print(f"   历史事件数: {len(state.history)}")

        if state.last_error:
            print(f"   ⚠️  错误: {state.last_error}")

    except Exception as e:
        print(f"\n❌ 回放失败!")
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 关闭运行时...")
        runtime.close()
        print("✓ 已关闭")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: poetry run python replay_trajectory.py <trajectory_file>")
        print()
        print("示例:")
        print("  poetry run python replay_trajectory.py trajectory.json")
        sys.exit(1)

    asyncio.run(replay(sys.argv[1]))
