#!/usr/bin/env python3
"""Summarize SEC-bench轨迹文件为便于复盘的文本/CSV/XLSX."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

FIELD_ORDER = [
    'step_id',
    'timestamp',
    'source',
    'kind',
    'thought',
    'command',
    'path',
    'view_range',
    'message',
    'exit_code',
    'output',
    'success',
]


def _shorten_line(text: str, max_length: int) -> str:
    text = ' '.join(text.split())
    if max_length > 0 and len(text) > max_length:
        return text[: max_length - 3] + '...'
    return text


def _format_block(content: str, max_lines: int, indent: str) -> Iterable[str]:
    lines = content.rstrip('\n').splitlines()
    if max_lines > 0 and len(lines) > max_lines:
        visible = lines[:max_lines]
        hidden_count = len(lines) - max_lines
        yield from (f'{indent}{line}' for line in visible)
        yield f'{indent}... ({hidden_count} more lines)'
    else:
        yield from (f'{indent}{line}' for line in lines)


def _interesting_args(args: dict | None) -> dict[str, object]:
    if not isinstance(args, dict):
        return {}
    keys = ['command', 'path', 'view_range', 'thought']
    return {k: args[k] for k in keys if k in args}


def _extract_exit_code(step: dict) -> int | None:
    extras = step.get('extras')
    if isinstance(extras, dict):
        metadata = extras.get('metadata')
        if isinstance(metadata, dict) and 'exit_code' in metadata:
            return metadata['exit_code']
    return None


def _build_row(
    step: dict,
    *,
    max_message: int,
    max_output_lines: int,
) -> dict[str, str] | None:
    # 跳过纯系统初始化指令
    if step.get('source') == 'agent' and step.get('action') == 'system':
        return None

    step_id = step.get('id')
    source = step.get('source', 'unknown')
    kind = step.get('action') or step.get('observation') or 'event'

    args = _interesting_args(step.get('args'))
    command = args.get('command')
    path = args.get('path')
    view_range = args.get('view_range')
    thought = args.get('thought')

    message = step.get('message')
    exit_code = _extract_exit_code(step)
    content = step.get('content')
    success = step.get('success')

    if message:
        condensed = _shorten_line(message, max_message)
        if command and condensed.startswith('Command `') and 'executed' in condensed:
            condensed = ''
    else:
        condensed = ''

    if content:
        output_lines = list(_format_block(content, max_output_lines, ''))
        output_str = '\n'.join(output_lines)
    else:
        output_str = ''

    if isinstance(view_range, Sequence):
        view_repr = ','.join(str(v) for v in view_range)
    else:
        view_repr = ''

    row = {
        'step_id': str(step_id),
        'timestamp': step.get('timestamp', ''),
        'source': source,
        'kind': kind,
        'thought': _shorten_line(str(thought), max_message) if thought else '',
        'command': command or '',
        'path': path or '',
        'view_range': view_repr,
        'message': condensed,
        'exit_code': '' if exit_code is None else str(exit_code),
        'output': output_str,
        'success': '' if success is None else str(success),
    }
    return row


def summarize_trace(
    path: Path,
    *,
    max_message: int,
    max_output_lines: int,
) -> list[dict[str, str]]:
    with path.open(encoding='utf-8') as fp:
        data = json.load(fp)
    summaries: list[dict[str, str]] = []
    for step in data:
        row = _build_row(
            step,
            max_message=max_message,
            max_output_lines=max_output_lines,
        )
        if row:
            summaries.append(row)
    return summaries


def rows_to_text(rows: Sequence[dict[str, str]]) -> str:
    blocks: list[str] = []
    for row in rows:
        header = f"[{int(row['step_id']):03d}] {row['source']}:{row['kind']}"
        lines = [header]
        if row['thought']:
            lines.append(f"  THOUGHT: {row['thought']}")
        if row['command']:
            lines.append(f"  CMD: {row['command']}")
        if row['path']:
            if row['view_range']:
                lines.append(f"  PATH: {row['path']} lines {row['view_range']}")
            else:
                lines.append(f"  PATH: {row['path']}")
        if row['message']:
            lines.append(f"  MSG: {row['message']}")
        if row['exit_code']:
            lines.append(f"  EXIT_CODE: {row['exit_code']}")
        if row['output']:
            lines.append('  OUTPUT:')
            lines.extend(f'    {line}' for line in row['output'].splitlines())
        if row['success']:
            lines.append(f"  SUCCESS: {row['success']}")
        blocks.append('\n'.join(lines))
    return '\n'.join(blocks)


def write_csv(rows: Sequence[dict[str, str]], out: Path | None) -> None:
    if out is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELD_ORDER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_ORDER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_xlsx(rows: Sequence[dict[str, str]], out: Path) -> None:
    try:
        from openpyxl import Workbook  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            '需要安装 openpyxl 才能导出为 XLSX，请先运行 `pip install openpyxl`。'
        ) from exc

    out.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = 'trace'
    ws.append(FIELD_ORDER)
    for row in rows:
        ws.append([row.get(field, '') for field in FIELD_ORDER])
    wb.save(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='提取SEC-bench轨迹关键步骤，输出文本/CSV/XLSX。',
    )
    parser.add_argument('trace_path', type=Path, help='轨迹JSON文件路径')
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='输出文件路径（默认打印到stdout）',
    )
    parser.add_argument(
        '--format',
        choices=['text', 'csv', 'xlsx'],
        default='text',
        help='输出格式（默认text）',
    )
    parser.add_argument(
        '--max-message',
        type=int,
        default=240,
        help='单条消息最大字符数（默认240，<=0表示不截断）',
    )
    parser.add_argument(
        '--max-output-lines',
        type=int,
        default=12,
        help='每步输出内容展示的最大行数（默认12，<=0表示全部展示）',
    )
    args = parser.parse_args()

    summaries = summarize_trace(
        args.trace_path,
        max_message=args.max_message,
        max_output_lines=args.max_output_lines,
    )

    if args.format == 'text':
        text = rows_to_text(summaries)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding='utf-8')
        else:
            print(text)
    elif args.format == 'csv':
        write_csv(summaries, args.output)
    else:  # xlsx
        if args.output is None:
            parser.error('导出 XLSX 时必须通过 -o 指定输出文件路径。')
        write_xlsx(summaries, args.output)


if __name__ == '__main__':
    main()
