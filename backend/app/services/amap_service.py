"""高德地图MCP服务封装"""

import threading
from typing import List, Dict, Any, Optional
from hello_agents.tools import MCPTool
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# 全局MCP工具实例
_amap_mcp_tool = None
# 路由层现在会经 asyncio.to_thread 从多个工作线程调用本模块的取实例函数，
# 因此「检查-构造-赋值」这段必须加锁（详见 get_amap_service 的注释）。
_amap_mcp_tool_lock = threading.Lock()


def get_amap_mcp_tool() -> MCPTool:
    """
    获取高德地图MCP工具实例(单例模式)
    
    Returns:
        MCPTool实例
    """
    global _amap_mcp_tool
    
    if _amap_mcp_tool is None:
        with _amap_mcp_tool_lock:
            if _amap_mcp_tool is None:
                settings = get_settings()

                if not settings.vite_amap_web_key:
                    raise ValueError("高德地图 API Key 未配置，请先在前端设置页完成配置")

                # 创建MCP工具
                _amap_mcp_tool = MCPTool(
                    name="amap",
                    description="高德地图服务,支持POI搜索、路线规划、天气查询等功能",
                    server_command=["uvx", "amap-mcp-server"],
                    env={"AMAP_MAPS_API_KEY": settings.vite_amap_web_key},
                    auto_expand=True  # 自动展开为独立工具
                )

                print(f"✅ 高德地图MCP工具初始化成功")
                print(f"   工具数量: {len(_amap_mcp_tool._available_tools)}")

                # 打印可用工具列表
                if _amap_mcp_tool._available_tools:
                    print("   可用工具:")
                    for tool in _amap_mcp_tool._available_tools[:5]:  # 只打印前5个
                        print(f"     - {tool.get('name', 'unknown')}")
                    if len(_amap_mcp_tool._available_tools) > 5:
                        print(f"     ... 还有 {len(_amap_mcp_tool._available_tools) - 5} 个工具")

    return _amap_mcp_tool


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        self.mcp_tool = get_amap_mcp_tool()
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        """
        搜索POI
        
        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内
            
        Returns:
            POI信息列表
        """
        try:
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_text_search",
                "arguments": {
                    "keywords": keywords,
                    "city": city,
                    "citylimit": str(citylimit).lower()
                }
            })
            
            # 解析结果
            # 注意: MCP工具返回的是字符串,需要解析
            # 这里简化处理,实际应该解析JSON
            print(f"POI搜索结果: {result[:200]}...")  # 打印前200字符
            
            # TODO: 解析实际的POI数据
            return []
            
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息列表
        """
        try:
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_weather",
                "arguments": {
                    "city": city
                }
            })
            
            print(f"天气查询结果: {result[:200]}...")
            
            # TODO: 解析实际的天气数据
            return []
            
        except Exception as e:
            print(f"❌ 天气查询失败: {str(e)}")
            return []
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线
        
        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)
            
        Returns:
            路线信息
        """
        try:
            # 根据路线类型选择工具
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }
            
            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
            
            # 构建参数
            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }
            
            # 公共交通需要城市参数
            if route_type == "transit":
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            else:
                # 其他路线类型也可以提供城市参数提高准确性
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments
            })
            
            print(f"路线规划结果: {result[:200]}...")
            
            # TODO: 解析实际的路线数据
            return {}
            
        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            arguments = {"address": address}
            if city:
                arguments["city"] = city

            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_geo",
                "arguments": arguments
            })

            print(f"地理编码结果: {result[:200]}...")

            # TODO: 解析实际的坐标数据
            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_search_detail",
                "arguments": {
                    "id": poi_id
                }
            })

            print(f"POI详情结果: {result[:200]}...")

            # 解析结果并提取图片
            import json
            import re

            # 尝试从结果中提取JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None
_amap_service_lock = threading.Lock()


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service

    if _amap_service is None:
        # 加锁的原因：路由层现在通过 asyncio.to_thread(get_amap_service) 调用本函数，
        # 并发首次请求会同时进入这里。若不加锁，「检查 - 构造 - 赋值」之间存在窗口，
        # 多个线程会各建一个 AmapService（每次构造都包含一次 MCP 服务发现往返），
        # 后写入的覆盖先写入的，多出来的实例被直接丢弃。
        with _amap_service_lock:
            if _amap_service is None:
                _amap_service = AmapService()

    return _amap_service


def reset_amap_service() -> None:
    """重置高德地图服务与 MCP 工具实例（用于运行时配置更新后热生效）。"""
    global _amap_service, _amap_mcp_tool
    with _amap_service_lock:
        _amap_service = None
    with _amap_mcp_tool_lock:
        _amap_mcp_tool = None


# ============ 酒店周边搜索（住宿定制功能，直接走高德 REST） ============

# 住宿类型 → 周边搜索关键词
_HOTEL_TYPE_KEYWORDS = {
    "民宿": "民宿",
    "青年旅舍": "青年旅舍",
}
# 未提供真实价格时按住宿类型估算（元/晚），仅用于排序参考
_HOTEL_TYPE_PRICE_FALLBACK = {
    "经济型酒店": 250,
    "舒适型酒店": 450,
    "豪华酒店": 900,
    "民宿": 350,
    "青年旅舍": 100,
}


def geocode_address(address: str, city: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """关键词地理编码，返回 {"longitude", "latitude", "name"} 或 None（同步函数）。"""
    import httpx

    settings = get_settings()
    params = {"key": settings.vite_amap_web_key, "address": address}
    if city:
        params["city"] = city
    try:
        resp = httpx.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params=params,
            timeout=8,
            trust_env=False,
        )
        data = resp.json()
        geocodes = data.get("geocodes") or []
        if data.get("status") == "1" and geocodes:
            loc = (geocodes[0].get("location") or "").split(",")
            if len(loc) == 2:
                return {
                    "longitude": float(loc[0]),
                    "latitude": float(loc[1]),
                    "name": address,
                }
    except Exception as e:
        print(f"❌ 酒店选点地理编码失败: {e}")
    return None


def _search_hotels_v5(api_key: str, location: str, radius: int, keyword: str) -> List[Dict[str, Any]]:
    """高德 v5 周边搜索（可返回评分/人均消费），失败返回空列表。"""
    import httpx

    params = {
        "key": api_key,
        "location": location,
        "radius": radius,
        "types": "100000",  # 住宿服务
        "page_size": 25,
        "page_num": 1,
        "show_fields": "business",
    }
    if keyword:
        params["keywords"] = keyword
    resp = httpx.get("https://restapi.amap.com/v5/place/around", params=params, timeout=8, trust_env=False)
    data = resp.json()
    if data.get("status") != "1":
        return []

    results = []
    for poi in data.get("pois") or []:
        biz = poi.get("business") or {}
        rating_raw = str(biz.get("rating") or "").strip()
        cost_raw = str(biz.get("cost") or "").strip()
        rating = None
        try:
            if rating_raw and rating_raw not in ("[]", "0"):
                rating = float(rating_raw)
        except ValueError:
            rating = None
        cost = None
        try:
            if cost_raw and cost_raw not in ("[]", "0"):
                cost = int(float(cost_raw))
        except ValueError:
            cost = None
        loc = (poi.get("location") or "").split(",")
        results.append({
            "name": poi.get("name", ""),
            "address": poi.get("address") or "",
            "longitude": float(loc[0]) if len(loc) == 2 else None,
            "latitude": float(loc[1]) if len(loc) == 2 else None,
            "rating": rating,
            "cost": cost,
            "distance_m": int(poi["distance"]) if str(poi.get("distance", "")).isdigit() else None,
            "hotel_type": (poi.get("type") or "").split(";")[0].split(":")[-1],
        })
    return results


def _search_hotels_v3(api_key: str, location: str, radius: int, keyword: str) -> List[Dict[str, Any]]:
    """高德 v3 周边搜索（无评分/价格字段），v5 失败时的回退。"""
    import httpx

    params = {
        "key": api_key,
        "location": location,
        "radius": radius,
        "types": "100000",
        "offset": 25,
        "page": 1,
    }
    if keyword:
        params["keywords"] = keyword
    resp = httpx.get("https://restapi.amap.com/v3/place/around", params=params, timeout=8, trust_env=False)
    data = resp.json()
    if data.get("status") != "1":
        return []

    results = []
    for poi in data.get("pois") or []:
        loc = (poi.get("location") or "").split(",")
        results.append({
            "name": poi.get("name", ""),
            "address": poi.get("address") or "",
            "longitude": float(loc[0]) if len(loc) == 2 else None,
            "latitude": float(loc[1]) if len(loc) == 2 else None,
            "rating": None,
            "cost": None,
            "distance_m": int(poi["distance"]) if str(poi.get("distance", "")).isdigit() else None,
            "hotel_type": (poi.get("type") or "").split(";")[0].split("|")[0].split(":")[-1],
        })
    return results


def search_hotels_around(
    city: str,
    center: Dict[str, Any],
    radius: int,
    accommodation_type: str,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    sort_mode: str = "cost_perf",
    limit: int = 8,
) -> Dict[str, Any]:
    """按中心点+半径搜索住宿候选，按评分/价格/性价比打分排序（同步函数）。

    Args:
        city: 城市（用于类型关键词兜底，当前搜索以坐标为准）
        center: {"longitude": float, "latitude": float, "name": str}
        radius: 搜索半径（米）
        accommodation_type: 住宿类型（决定搜索关键词与价格估算兜底）
        price_min/price_max: 每晚价格区间（元），仅过滤有真实价格数据的候选
        sort_mode: rating / price / cost_perf
        limit: 返回数量

    Returns:
        {"candidates": [HotelCandidate dict], "total_found": int, "price_estimated": bool}
    """
    settings = get_settings()
    api_key = settings.vite_amap_web_key
    location_str = f"{center['longitude']},{center['latitude']}"
    keyword = _HOTEL_TYPE_KEYWORDS.get(accommodation_type, "酒店")

    raw = _search_hotels_v5(api_key, location_str, radius, keyword)
    source = "v5"
    if not raw:
        raw = _search_hotels_v3(api_key, location_str, radius, keyword)
        source = "v3"

    if not raw:
        return {"candidates": [], "total_found": 0, "price_estimated": False, "source": source}

    fallback_price = _HOTEL_TYPE_PRICE_FALLBACK.get(accommodation_type, 300)
    price_estimated = False

    # 价格过滤（仅对有真实价格的候选生效）
    filtered = []
    for item in raw:
        if item["cost"] is not None:
            if price_min is not None and item["cost"] < price_min:
                continue
            if price_max is not None and item["cost"] > price_max:
                continue
        else:
            item["cost"] = fallback_price
            item["price_is_estimate"] = True
            price_estimated = True
        filtered.append(item)

    if not filtered:
        return {"candidates": [], "total_found": len(raw), "price_estimated": price_estimated, "source": source}

    # 归一化打分
    costs = [it["cost"] for it in filtered]
    c_min, c_max = min(costs), max(costs)
    for it in filtered:
        it["rating_score"] = round(it["rating"] / 5.0, 3) if it["rating"] else 0.0
        if c_max > c_min:
            it["price_score"] = round(1.0 - (it["cost"] - c_min) / (c_max - c_min), 3)
        else:
            it["price_score"] = 1.0
        it["total_score"] = round(0.6 * it["rating_score"] + 0.4 * it["price_score"], 3)

    if sort_mode == "rating":
        filtered.sort(key=lambda it: (it["rating_score"], it["total_score"]), reverse=True)
    elif sort_mode == "price":
        filtered.sort(key=lambda it: (it["price_score"], it["total_score"]), reverse=True)
    else:  # cost_perf
        filtered.sort(key=lambda it: it["total_score"], reverse=True)

    candidates = []
    for it in filtered[:limit]:
        candidates.append({
            "name": it["name"],
            "address": it["address"],
            "location": (
                {"longitude": it["longitude"], "latitude": it["latitude"]}
                if it["longitude"] is not None else None
            ),
            "hotel_type": it["hotel_type"] or accommodation_type,
            "rating": it["rating"],
            "estimated_cost": it["cost"],
            "distance_m": it["distance_m"],
            "rating_available": it["rating"] is not None,
            "rating_score": it["rating_score"],
            "price_score": it["price_score"],
            "total_score": it["total_score"],
        })

    return {
        "candidates": candidates,
        "total_found": len(raw),
        "price_estimated": price_estimated,
        "source": source,
    }
