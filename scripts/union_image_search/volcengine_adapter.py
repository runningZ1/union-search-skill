#!/usr/bin/env python3
"""
火山引擎图片搜索适配器

将火山引擎图片搜索 API 适配到 union_image_search 架构
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def load_api_key() -> Optional[str]:
    """加载火山引擎 API Key"""
    api_key = os.getenv("VOLCENGINE_API_KEY")
    if api_key:
        return api_key

    # 尝试从 .env 文件读取
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == "VOLCENGINE_API_KEY":
                                return value.strip().strip('"').strip("'")
            except Exception:
                pass

    return None


class VolcengineImageAdapter:
    """火山引擎图片搜索适配器"""

    def __init__(self, work_dir: str):
        """
        初始化适配器

        Args:
            work_dir: 工作目录,用于保存下载的图片
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = load_api_key()
        self.base_url = "https://open.feedcoopapi.com/search_api/web_search"

    def search(self, keyword: str, search_limits: int = 5) -> List[Dict[str, Any]]:
        """
        搜索图片

        Args:
            keyword: 搜索关键词
            search_limits: 搜索数量限制 (最多5张)

        Returns:
            图片信息列表
        """
        if not self.api_key:
            print("Warning: VOLCENGINE_API_KEY not found", file=sys.stderr)
            return []

        # 调用火山引擎图片搜索 API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "Query": keyword,
            "SearchType": "image",
            "Count": min(search_limits, 5),  # 最多5条
            "Filter": {},
            "QueryControl": {
                "QueryRewrite": False
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # 解析响应,转换为标准格式（官方: Result.ImageResults[].Image.Url）
            image_infos = []
            images = result.get("Result", {}).get("ImageResults", [])

            for idx, img in enumerate(images):
                image_obj = img.get("Image") or {}
                image_url = image_obj.get("Url", "")
                if not image_url:
                    continue

                image_info = {
                    'identifier': f"volcengine_{idx}",
                    'candidate_urls': [image_url],
                    'raw_data': {
                        'title': img.get("Title", ""),
                        'site_name': img.get("SiteName", ""),
                        'source_url': img.get("Url", ""),
                        'publish_time': img.get("PublishTime", ""),
                        'width': image_obj.get("Width", 0),
                        'height': image_obj.get("Height", 0),
                        'shape': image_obj.get("Shape", ""),
                        'rank_score': img.get("RankScore", 0),
                    }
                }
                image_infos.append(image_info)

            return image_infos

        except Exception as e:
            print(f"Volcengine search error: {e}", file=sys.stderr)
            return []

    def download(self, image_infos: List[Dict[str, Any]], num_threadings: int = 5) -> None:
        """
        下载图片

        Args:
            image_infos: 图片信息列表
            num_threadings: 下载线程数 (未使用,保持接口一致)
        """
        for idx, info in enumerate(image_infos):
            urls = info.get('candidate_urls', [])
            if not urls:
                continue

            image_url = urls[0]
            try:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()

                # 确定文件扩展名
                content_type = response.headers.get('Content-Type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = 'jpg'
                elif 'png' in content_type:
                    ext = 'png'
                elif 'gif' in content_type:
                    ext = 'gif'
                elif 'webp' in content_type:
                    ext = 'webp'
                else:
                    ext = 'jpg'  # 默认

                # 保存文件
                filename = f"{idx+1:08d}.{ext}"
                filepath = self.work_dir / filename
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                # 更新 file_path
                info['file_path'] = str(filepath)

            except Exception as e:
                print(f"Failed to download {image_url}: {e}", file=sys.stderr)


def search_volcengine_images(keyword: str, num_images: int, output_dir: str,
                             num_threads: int = 5, save_meta: bool = True) -> Dict[str, Any]:
    """
    搜索火山引擎图片 (兼容 union_image_search 接口)

    Args:
        keyword: 搜索关键词
        num_images: 图片数量 (最多5张)
        output_dir: 输出目录
        num_threads: 下载线程数
        save_meta: 是否保存元数据

    Returns:
        搜索结果字典
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(' ', '_').replace('/', '_')
    platform_dir = os.path.join(output_dir, f"volcengine_{safe_keyword}_{timestamp}")

    target_num = 5 if num_images <= 0 else min(num_images, 5)

    print(f"\n{'='*70}")
    print(f"平台: VOLCENGINE | 关键词: '{keyword}' | 目标: {target_num} 张")
    print(f"{'='*70}")

    try:
        adapter = VolcengineImageAdapter(platform_dir)

        print(f"[1/2] 正在搜索...")
        image_infos = adapter.search(keyword, search_limits=target_num)

        if not image_infos:
            print(f"✗ 未找到图片")
            return {
                'platform': 'volcengine',
                'keyword': keyword,
                'success': False,
                'error': '未找到图片',
                'downloaded': 0,
                'metadata': [],
                'output_dir': platform_dir
            }

        print(f"✓ 找到 {len(image_infos)} 张图片")

        print(f"[2/2] 正在下载...")
        adapter.download(image_infos, num_threadings=num_threads)

        # 统计下载成功的图片
        downloaded_count = sum(1 for info in image_infos if 'file_path' in info)

        # 保存元数据
        metadata_file = None
        if save_meta and image_infos:
            metadata = {
                'platform': 'volcengine',
                'keyword': keyword,
                'timestamp': datetime.now().isoformat(),
                'total_images': len(image_infos),
                'images': image_infos
            }
            metadata_file = os.path.join(platform_dir, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"✓ 成功下载 {downloaded_count} 张图片")
        print(f"✓ 保存位置: {platform_dir}")

        return {
            'platform': 'volcengine',
            'keyword': keyword,
            'success': True,
            'downloaded': downloaded_count,
            'found': len(image_infos),
            'metadata': image_infos,
            'output_dir': platform_dir,
            'metadata_file': metadata_file
        }

    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return {
            'platform': 'volcengine',
            'keyword': keyword,
            'success': False,
            'error': str(e),
            'downloaded': 0,
            'metadata': [],
            'output_dir': platform_dir
        }
