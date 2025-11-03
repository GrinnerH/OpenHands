#!/usr/bin/env python3
"""
从 output.jsonl 提取轨迹为标准格式
这个脚本不需要 openhands 依赖，可以直接运行
"""

import json
import sys
import os

def extract_trajectory(jsonl_file: str, instance_id: str, output_file: str):
    """从 output.jsonl 提取指定实例的轨迹"""
    print(f"📂 读取文件: {jsonl_file}")
    print(f"🔍 查找实例: {instance_id}")

    found = False
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            if data['instance_id'] == instance_id:
                history = data['history']

                # 确保输出目录存在
                output_dir = os.path.dirname(output_file)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                # 保存为标准轨迹格式
                with open(output_file, 'w') as out:
                    json.dump(history, out, indent=2)

                print(f"\n✓ 提取成功!")
                print(f"  实例ID: {instance_id}")
                print(f"  事件总数: {len(history)}")
                print(f"  保存位置: {output_file}")

                # 统计事件类型
                action_types = {}
                for event in history:
                    action = event.get('action', 'unknown')
                    action_types[action] = action_types.get(action, 0) + 1

                print(f"\n  事件类型分布:")
                for action, count in sorted(action_types.items(), key=lambda x: -x[1]):
                    print(f"    - {action}: {count}")

                found = True
                break

    if not found:
        print(f"\n✗ 未找到实例: {instance_id}")
        return False

    return True

def list_instances(jsonl_file: str):
    """列出所有实例"""
    print(f"📋 读取文件: {jsonl_file}\n")

    instances = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            instances.append({
                'id': data['instance_id'],
                'events': len(data.get('history', [])),
                'error': data.get('error')
            })

    print(f"找到 {len(instances)} 个实例:\n")
    for i, inst in enumerate(instances, 1):
        error_str = f" ❌ {inst['error'][:50]}..." if inst['error'] else " ✓"
        print(f"{i}. {inst['id']}")
        print(f"   事件数: {inst['events']}{error_str}")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  列出实例: python extract_trajectory.py list <jsonl_file>")
        print("  提取轨迹: python extract_trajectory.py <jsonl_file> <instance_id> [output_file]")
        print()
        print("说明:")
        print("  - 如果不指定 output_file，将自动保存到:")
        print("    <jsonl_dir>/Trace/{instance_id}/{instance_id}.json")
        print()
        print("示例:")
        print("  # 列出所有实例")
        print("  python extract_trajectory.py list output.jsonl")
        print()
        print("  # 提取到默认位置（推荐）")
        print("  python extract_trajectory.py output.jsonl gpac.cve-2023-5586")
        print("  # 会保存到: <output.jsonl所在目录>/Trace/gpac.cve-2023-5586/gpac.cve-2023-5586.json")
        print()
        print("  # 提取到自定义位置")
        print("  python extract_trajectory.py output.jsonl gpac.cve-2023-5586 /tmp/trace.json")
        sys.exit(1)

    if sys.argv[1] == 'list':
        if len(sys.argv) != 3:
            print("用法: python extract_trajectory.py list <jsonl_file>")
            sys.exit(1)
        list_instances(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print("用法: python extract_trajectory.py <jsonl_file> <instance_id> [output_file]")
            sys.exit(1)

        jsonl_file = sys.argv[1]
        instance_id = sys.argv[2]

        # 如果没有指定输出文件，自动生成在 Trace/{instance_id}/ 子目录
        if len(sys.argv) == 3:
            jsonl_dir = os.path.dirname(os.path.abspath(jsonl_file))
            # 创建 Trace/{instance_id} 目录结构
            trace_dir = os.path.join(jsonl_dir, 'Trace', instance_id)
            output_file = os.path.join(trace_dir, f"{instance_id}.json")
        else:
            output_file = sys.argv[3]

        extract_trajectory(jsonl_file, instance_id, output_file)
