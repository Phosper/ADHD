# 数据集链接核验（2026-11-09）

- 范围：`datasets/` 下 5 个 Markdown/CSV 文件中的全部链接
- 方法：`curl -L -I`，跟随重定向，25 秒超时，普通浏览器 User-Agent
- 结果：51 个唯一 URL，**51/51 都能解析到最终地址**，没有 DNS 失败、404 或超时

## 状态统计

| HTTP 状态 | 数量 | 说明 |
| --- | ---: | --- |
| 200 | 45 | 正常 |
| 202 | 5 | IEEE Xplore 的反爬挑战页，DOI 和文档地址有效 |
| 403 | 1 | ACM DOI 的反爬拦截，浏览器可访问，DOI 本身有效 |

## 需要说明的链接

| 链接 | 状态 | 最终地址 | 判断 |
| --- | ---: | --- | --- |
| `https://doi.org/10.1145/3083187.3083220` | 403 | `https://dl.acm.org/doi/10.1145/3083187.3083220` | MMSys 2017 论文；Crossref 已确认 DOI，ACM 只拦截自动请求，不是死链 |
| `https://doi.org/10.1109/ACII.2017.8273615` | 202 | `https://ieeexplore.ieee.org/document/8273615/` | IEEE 反爬挑战，DOI 有效 |
| `https://doi.org/10.1109/APSIPAASC58517.2023.10317512` | 202 | `https://ieeexplore.ieee.org/document/10317512/` | IEEE 反爬挑战，DOI 有效 |
| `https://doi.org/10.1109/ICASSP39728.2021.9413391` | 202 | `https://ieeexplore.ieee.org/document/9413391/` | IEEE 反爬挑战，DOI 有效 |
| `https://doi.org/10.1109/ICOSP.2014.7015071` | 202 | `https://ieeexplore.ieee.org/document/7015071/` | IEEE 反爬挑战，DOI 有效 |
| `https://doi.org/10.1109/ODYSSEY.2006.248084` | 202 | `https://ieeexplore.ieee.org/document/4013501/` | IEEE 反爬挑战，DOI 有效 |

## 本次修正

- `http://dl.acm.org/citation.cfm?id=3083220`（旧 ACM 链接，自动访问 403）替换为 `https://doi.org/10.1145/3083187.3083220`。
- `https://www.sciencedirect.com/science/article/pii/S0167639321001308`（ScienceDirect 自动访问 403）替换为 `https://doi.org/10.1016/j.specom.2021.11.006`，DOI 解析返回 200。

## 未验证

- 没有实际下载每个数据集的全部文件，只确认入口和元数据页可达。
- 没有验证 Hugging Face gated 申请是否通过、Google Drive 权限、百度网盘提取码是否仍有效。
- 没有对许可做法律意见；页面可达不代表允许商用或再分发。

逐条结果见 [`link-check-2026-11-09.csv`](link-check-2026-11-09.csv)。
