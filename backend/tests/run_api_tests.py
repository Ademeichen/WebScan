#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行API测试脚本
"""
import asyncio
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

from tests.test_all_apis import run_all_tests

async def main():
    try:
        passed, failed, total = await run_all_tests()
        print(f'\n测试结果: {passed}/{total} 通过, {failed} 失败')
        return 0 if failed == 0 else 1
    except Exception as e:
        print(f'测试执行错误: {e}')
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
