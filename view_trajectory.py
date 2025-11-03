#!/usr/bin/env python3
"""
查看轨迹历史记录（不执行，只展示）

用法:
  python view_trajectory.py <trajectory_file>
  python view_trajectory.py <trajectory_file> --summary  # 只显示摘要
  python view_trajectory.py <trajectory_file> --actions  # 只显示 actions
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def parse_timestamp(ts_str):
    """解析时间戳"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts_str[:8] if len(ts_str) > 8 else ts_str


def view_summary(events):
    """显示轨迹摘要"""
    print("=" * 80)
    print("轨迹摘要")
    print("=" * 80)
    print(f"总事件数: {len(events)}\n")

    # 统计事件类型
    action_types = {}
    sources = {}
    for event in events:
        action = event.get('action', 'unknown')
        source = event.get('source', 'unknown')
        action_types[action] = action_types.get(action, 0) + 1
        sources[source] = sources.get(source, 0) + 1

    print("事件类型分布:")
    for action, count in sorted(action_types.items(), key=lambda x: -x[1]):
        print(f"  {action:20s}: {count:4d}")

    print(f"\n事件来源分布:")
    for source, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {source:20s}: {count:4d}")

    # 找到第一个用户消息
    for event in events:
        if event.get('action') == 'message' and event.get('source') == 'user':
            msg = event.get('message', event.get('args', {}).get('content', ''))
            print(f"\n初始任务:")
            print(f"  {msg[:200]}{'...' if len(msg) > 200 else ''}")
            break


def view_actions(events):
    """只显示 action 事件"""
    print("=" * 80)
    print("Action 事件列表")
    print("=" * 80)

    action_count = 0
    for i, event in enumerate(events):
        action = event.get('action')
        if not action:
            continue

        action_count += 1
        timestamp = parse_timestamp(event.get('timestamp', ''))
        source = event.get('source', 'unknown')

        print(f"\n[{action_count}] {timestamp} | {source} | {action}")

        # 显示具体内容
        if action == 'message':
            msg = event.get('message', event.get('args', {}).get('content', ''))
            print(f"    消息: {msg[:100]}{'...' if len(msg) > 100 else ''}")

        elif action == 'run':
            cmd = event.get('args', {}).get('command', '')
            print(f"    命令: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")

        elif action == 'str_replace_editor':
            args = event.get('args', {})
            cmd_type = args.get('command', '')
            path = args.get('path', '')
            print(f"    编辑器: {cmd_type} {path}")

        elif action == 'finish':
            msg = event.get('args', {}).get('message', '')
            print(f"    完成消息: {msg[:100]}{'...' if len(msg) > 100 else ''}")

    print(f"\n总共 {action_count} 个 action 事件")


def view_full(events):
    """显示完整详细信息"""
    print("=" * 80)
    print("完整轨迹")
    print("=" * 80)

    for i, event in enumerate(events, 1):
        print(f"\n{'─' * 80}")
        print(f"事件 #{i}")
        print(f"{'─' * 80}")

        timestamp = event.get('timestamp', 'N/A')
        action = event.get('action', event.get('observation', 'unknown'))
        source = event.get('source', 'unknown')

        print(f"时间: {timestamp}")
        print(f"类型: {action}")
        print(f"来源: {source}")

        # 显示消息
        if 'message' in event:
            print(f"\n消息:")
            print(f"  {event['message'][:300]}{'...' if len(event.get('message', '')) > 300 else ''}")

        # 显示参数
        if 'args' in event and event['args']:
            print(f"\n参数:")
            args = event['args']
            for key, value in list(args.items())[:5]:  # 只显示前5个参数
                if isinstance(value, str):
                    val_str = value[:100] + '...' if len(value) > 100 else value
                else:
                    val_str = str(value)[:100]
                print(f"  {key}: {val_str}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    trajectory_file = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'full'

    # 读取轨迹文件
    traj_path = Path(trajectory_file)
    if not traj_path.exists():
        print(f"❌ 文件不存在: {trajectory_file}")
        sys.exit(1)

    print(f"📂 读取轨迹: {trajectory_file}\n")

    with open(traj_path, 'r') as f:
        events = json.load(f)

    if not isinstance(events, list):
        print(f"❌ 轨迹格式错误：应该是事件数组，但得到 {type(events)}")
        sys.exit(1)

    # 根据模式显示
    if mode == '--summary':
        view_summary(events)
    elif mode == '--actions':
        view_actions(events)
    else:
        view_summary(events)
        print("\n\n")
        view_actions(events)
        print("\n\n提示: 使用 --summary 只看摘要，--actions 只看操作")


if __name__ == '__main__':
    main()
