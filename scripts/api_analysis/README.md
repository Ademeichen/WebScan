# API分析脚本

本目录包含用于分析前后端API兼容性的脚本。

## 文件说明

### analyze_all_apis_fixed.py ⭐推荐使用
完整的API分析脚本（修复版），用于分析前后端所有API接口的兼容性。

**功能：**
- 提取后端所有API接口
- 提取前端所有API调用
- 匹配前后端API
- 生成详细的兼容性报告

**使用方法：**
```bash
python scripts\api_analysis\analyze_all_apis_fixed.py
```

**输出：**
- 控制台输出：匹配成功的API、未匹配的API
- 文件输出：`.trae\documents\all_apis_analysis_fixed.json`

### analyze_all_apis.py
原始的API分析脚本，已被 `analyze_all_apis_fixed.py` 替代。

**状态：** 已废弃，建议使用 `analyze_all_apis_fixed.py`

### analyze_backend_apis.py
专门用于分析后端API接口的脚本。

**功能：**
- 扫描后端所有API路由文件
- 提取API定义（方法、路径、参数）
- 生成后端API清单

**使用方法：**
```bash
python scripts\api_analysis\analyze_backend_apis.py
```

### analyze_frontend_usage.py
专门用于分析前端API使用情况的脚本。

**功能：**
- 扫描前端Vue组件
- 识别API调用
- 分析API使用频率

**使用方法：**
```bash
python scripts\api_analysis\analyze_frontend_usage.py
```

### match_apis_complete.py
完整的API匹配脚本，确保前端所有API都与后端匹配。

**功能：**
- 匹配前后端API
- 识别未匹配的接口
- 提供修复建议

**使用方法：**
```bash
python scripts\api_analysis\match_apis_complete.py
```

### check_api_compatibility.py
前后端API接口兼容性校验脚本。

**功能：**
- 读取API分析结果
- 验证路径匹配
- 生成兼容性报告

**使用方法：**
```bash
python scripts\api_analysis\check_api_compatibility.py
```

## 工作流程

推荐的工作流程：

1. **运行完整分析**
   ```bash
   python scripts\api_analysis\analyze_all_apis_fixed.py
   ```

2. **查看结果**
   - 控制台输出会显示匹配统计
   - 详细结果保存在 `.trae\documents\all_apis_analysis_fixed.json`

3. **修复未匹配的API**
   - 根据分析结果修改前端API定义
   - 或添加缺失的后端接口

4. **重新验证**
   ```bash
   python scripts\api_analysis\analyze_all_apis_fixed.py
   ```

## 统计数据

最新分析结果（2026-03-13）：

| 指标 | 数值 |
|------|------|
| 后端API总数 | 141 |
| 前端API总数 | 91 |
| 匹配成功 | 91 |
| 前端未匹配 | 0 |
| 后端未匹配 | 51 |
| 前端匹配率 | 100% ✅ |

## 注意事项

1. 所有脚本都使用绝对路径，请确保项目根目录为 `d:\AI_WebSecurity`
2. 分析结果会保存在 `.trae\documents\` 目录下
3. 修改API后，建议重新运行分析脚本验证
4. 前端API定义文件：`front\src\utils\api.js`
5. 后端API路由文件：`backend\api\` 目录

## 相关文件

- `front\src\utils\api.js` - 前端API定义
- `backend\api\` - 后端API路由
- `.trae\documents\all_apis_analysis_fixed.json` - 最新分析结果
