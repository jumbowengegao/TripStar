"""数据模型定义"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date


# ============ 请求模型 ============

class CityStay(BaseModel):
    """单城市停留配置"""
    city: str = Field(..., description="城市名称")
    days: int = Field(..., description="在该城市停留天数", ge=1, le=15)


class Location(BaseModel):
    """地理位置"""
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")


class HotelSelection(BaseModel):
    """用户指定的住宿选择（来自前端 HotelPicker）"""
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Optional[Location] = Field(default=None, description="酒店经纬度")
    type: str = Field(default="", description="住宿类型")
    rating: Optional[str] = Field(default="", description="评分")
    estimated_cost: int = Field(default=0, description="预估费用(元/晚)")


class SelectedAttraction(BaseModel):
    """用户在景点选择页勾选的景点（来自前端 AttractionPicker）"""
    name: str = Field(..., description="景点名称(与候选列表中的 name 一致)")
    name_zh: str = Field(default="", description="中文简体名称(用于地理编码)")
    name_en: str = Field(default="", description="英文名称(用于 Google 编码)")
    location: Optional[Location] = Field(default=None, description="景点经纬度")
    duration: Optional[int] = Field(default=None, description="建议游玩时长(分钟)")
    reason: str = Field(default="", description="小红书用户评价/避坑指南")
    reservation_required: bool = Field(default=False, description="是否需要预约")
    reservation_tips: str = Field(default="", description="预约提示")
    region: str = Field(default="", description="所属区域(行政区/商圈)")


class DayPlanAssignment(BaseModel):
    """用户在行程规划弹窗中排好的某一天景点顺序"""
    day: int = Field(..., ge=1, le=30, description="第几天(1 开始)")
    attraction_names: List[str] = Field(default=[], description="该天要游览的景点名，按游览顺序排列")


class AttractionSearchRequest(BaseModel):
    """景点候选检索请求（小红书检索 + 按区域分组）"""
    city: str = Field(..., description="目的地城市", example="西安")
    preferences: List[str] = Field(default=[], description="偏好关键词", example=["历史文化"])
    language: str = Field(default="zh", description="输出语言(zh/en/ja)")
    limit: int = Field(default=18, ge=3, le=30, description="最多返回景点数")


class AttractionOption(BaseModel):
    """区域分组下的单个景点候选"""
    name: str = Field(..., description="景点名称(按目标语言)")
    name_zh: str = Field(default="", description="中文简体名称")
    name_en: str = Field(default="", description="英文名称")
    reason: str = Field(default="", description="小红书真实评价/避坑指南")
    duration: Optional[int] = Field(default=None, description="建议游玩时长(分钟)")
    reservation_required: bool = Field(default=False, description="是否需要提前预约")
    reservation_tips: str = Field(default="", description="预约提示")
    mention_count: int = Field(default=0, description="小红书笔记提及次数")
    location: Optional[Location] = Field(default=None, description="经纬度")
    address: str = Field(default="", description="地址")
    rating: Optional[str] = Field(default="", description="高德评分(可能为空)")
    region: str = Field(default="", description="所属区域")


class AttractionRegionGroup(BaseModel):
    """按区域聚合的景点分组"""
    region: str = Field(..., description="区域名称(行政区/商圈)")
    attractions: List[AttractionOption] = Field(default=[], description="该区域下的景点列表")


class AttractionSearchResponse(BaseModel):
    """景点候选检索响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="提示信息(降级原因等)")
    city: str = Field(default="", description="城市")
    regions: List[AttractionRegionGroup] = Field(default=[], description="按区域分组的景点")


class HotelCandidatesRequest(BaseModel):
    """酒店候选搜索请求"""
    city: str = Field(..., description="所在城市", example="西安")
    keywords: str = Field(default="", description="位置关键词(商圈/地标/地址)，与 location 二选一")
    location: Optional[Location] = Field(default=None, description="中心点坐标(地图选点)")
    radius: int = Field(default=3000, ge=500, le=10000, description="搜索半径(米)")
    accommodation_type: str = Field(default="经济型酒店", description="住宿类型")
    price_min: Optional[int] = Field(default=None, ge=0, description="每晚价格下限(元)")
    price_max: Optional[int] = Field(default=None, ge=0, description="每晚价格上限(元)")
    sort_mode: str = Field(default="cost_perf", description="排序: rating/price/cost_perf")
    limit: int = Field(default=8, ge=1, le=20, description="返回候选数量")

    @model_validator(mode='after')
    def check_center(self):
        if not self.location and not (self.keywords or '').strip():
            raise ValueError("必须提供 location(地图选点) 或 keywords(位置关键词) 之一")
        return self


class HotelCandidate(BaseModel):
    """单个酒店候选"""
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度")
    hotel_type: str = Field(default="", description="住宿类型")
    rating: Optional[float] = Field(default=None, description="评分(0-5)，数据不可用时为 null")
    estimated_cost: Optional[int] = Field(default=None, description="预估价格(元/晚)")
    distance_m: Optional[int] = Field(default=None, description="距中心点距离(米)")
    rating_available: bool = Field(default=False, description="评分数据是否可用")
    rating_score: float = Field(default=0.0, description="评分归一化得分(0-1)")
    price_score: float = Field(default=0.5, description="价格归一化得分(0-1，越高越便宜)")
    total_score: float = Field(default=0.0, description="综合得分(0-1)")


class HotelCandidatesResponse(BaseModel):
    """酒店候选搜索响应"""
    success: bool = Field(default=True)
    message: str = Field(default="")
    center: Optional[Location] = Field(default=None, description="搜索中心点")
    center_name: str = Field(default="", description="中心点名称(关键词选点时)")
    radius: int = Field(default=3000, description="搜索半径(米)")
    sort_mode: str = Field(default="cost_perf", description="排序模式")
    total_found: int = Field(default=0, description="搜索到的酒店总数")
    candidates: List[HotelCandidate] = Field(default=[], description="候选列表")


class TripRequest(BaseModel):
    """旅行规划请求"""
    city: str = Field(default="", description="目的地城市(单城市兼容)", example="北京")
    cities: List[CityStay] = Field(default=[], description="多城市行程配置")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD", example="2025-06-01")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD", example="2025-06-03")
    travel_days: int = Field(..., description="旅行天数", ge=1, le=30, example=3)
    transportation: str = Field(..., description="交通方式", example="公共交通")
    accommodation: str = Field(..., description="住宿偏好", example="经济型酒店")
    preferences: List[str] = Field(default=[], description="旅行偏好标签", example=["历史文化", "美食"])
    free_text_input: Optional[str] = Field(default="", description="额外要求", example="希望多安排一些博物馆")
    language: Optional[str] = Field(default="zh", description="输出语言(zh/en/ja)", example="en")
    user_id: Optional[str] = Field(default="", description="用户唯一标识(前端生成,用于记忆库)")
    hotel_selection: Optional[HotelSelection] = Field(default=None, description="用户指定的住宿(可选,提供后行程将使用该酒店)")
    selected_attractions: Optional[List[SelectedAttraction]] = Field(default=None, description="用户勾选的景点(可选,提供后跳过景点检索)")
    daily_plan: Optional[List[DayPlanAssignment]] = Field(default=None, description="用户排好的每日景点顺序(可选,最高优先级约束)")

    @model_validator(mode='after')
    def normalize_cities(self):
        """兼容处理: 如果只填了 city 没填 cities, 自动转换"""
        if not self.cities and self.city:
            self.cities = [CityStay(city=self.city, days=self.travel_days)]
        if self.cities and not self.city:
            self.city = self.cities[0].city
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "city": "北京",
                "cities": [{"city": "北京", "days": 2}, {"city": "西安", "days": 3}],
                "start_date": "2025-06-01",
                "end_date": "2025-06-05",
                "travel_days": 5,
                "transportation": "公共交通",
                "accommodation": "经济型酒店",
                "preferences": ["历史文化", "美食"],
                "free_text_input": "希望多安排一些博物馆"
            }
        }


class POISearchRequest(BaseModel):
    """POI搜索请求"""
    keywords: str = Field(..., description="搜索关键词", example="故宫")
    city: str = Field(..., description="城市", example="北京")
    citylimit: bool = Field(default=True, description="是否限制在城市范围内")


class RouteRequest(BaseModel):
    """路线规划请求"""
    origin_address: str = Field(..., description="起点地址", example="北京市朝阳区阜通东大街6号")
    destination_address: str = Field(..., description="终点地址", example="北京市海淀区上地十街10号")
    origin_city: Optional[str] = Field(default=None, description="起点城市")
    destination_city: Optional[str] = Field(default=None, description="终点城市")
    route_type: str = Field(default="walking", description="路线类型: walking/driving/transit")


# ============ 响应模型 ============

class Attraction(BaseModel):
    """景点信息"""
    name: str = Field(..., description="景点名称")
    address: str = Field(..., description="地址")
    location: Location = Field(..., description="经纬度坐标")
    visit_duration: int = Field(..., description="建议游览时间(分钟)")
    description: str = Field(..., description="景点描述")
    category: Optional[str] = Field(default="景点", description="景点类别")
    rating: Optional[float] = Field(default=None, description="评分")
    photos: Optional[List[str]] = Field(default_factory=list, description="景点图片URL列表")
    poi_id: Optional[str] = Field(default="", description="POI ID")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    ticket_price: int = Field(default=0, description="门票价格(元)")
    reservation_required: Optional[bool] = Field(default=False, description="是否需要提前预约")
    reservation_tips: Optional[str] = Field(default="", description="预约提示信息")


class Meal(BaseModel):
    """餐饮信息"""
    type: str = Field(..., description="餐饮类型: breakfast/lunch/dinner/snack")
    name: str = Field(..., description="餐饮名称")
    address: Optional[str] = Field(default=None, description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度坐标")
    description: Optional[str] = Field(default=None, description="描述")
    estimated_cost: int = Field(default=0, description="预估费用(元)")


class Hotel(BaseModel):
    """酒店信息"""
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Optional[Location] = Field(default=None, description="酒店位置")
    price_range: str = Field(default="", description="价格范围")
    rating: str = Field(default="", description="评分")
    distance: str = Field(default="", description="距离景点距离")
    type: str = Field(default="", description="酒店类型")
    estimated_cost: int = Field(default=0, description="预估费用(元/晚)")


class DayPlan(BaseModel):
    """单日行程"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_index: int = Field(..., description="第几天(从0开始)")
    city: str = Field(default="", description="当日所在城市")
    is_transfer_day: bool = Field(default=False, description="是否为城际移动日")
    transfer_info: Optional[str] = Field(default="", description="城际交通信息")
    description: str = Field(..., description="当日行程描述")
    transportation: str = Field(..., description="交通方式")
    accommodation: str = Field(..., description="住宿")
    hotel: Optional[Hotel] = Field(default=None, description="推荐酒店")
    attractions: List[Attraction] = Field(default=[], description="景点列表")
    meals: List[Meal] = Field(default=[], description="餐饮列表")


class WeatherInfo(BaseModel):
    """天气信息"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    city: str = Field(default="", description="所在城市")
    day_weather: str = Field(default="", description="白天天气")
    night_weather: str = Field(default="", description="夜间天气")
    day_temp: Union[int, str] = Field(default=0, description="白天温度")
    night_temp: Union[int, str] = Field(default=0, description="夜间温度")
    wind_direction: str = Field(default="", description="风向")
    wind_power: str = Field(default="", description="风力")

    @field_validator('day_temp', 'night_temp', mode='before')
    @classmethod
    def parse_temperature(cls, v):
        """解析温度,移除°C等单位"""
        if v is None:
            return 0
        if isinstance(v, str):
            # 移除°C, ℃等单位符号
            v = v.replace('°C', '').replace('℃', '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v


class Budget(BaseModel):
    """预算信息"""
    total_attractions: int = Field(default=0, description="景点门票总费用")
    total_hotels: int = Field(default=0, description="酒店总费用")
    total_meals: int = Field(default=0, description="餐饮总费用")
    total_transportation: int = Field(default=0, description="交通总费用")
    total_inter_city_transport: int = Field(default=0, description="城际交通总费用")
    total: int = Field(default=0, description="总费用")


class TripPlan(BaseModel):
    """旅行计划"""
    city: str = Field(..., description="主城市(兼容)/首个城市")
    cities: List[str] = Field(default=[], description="所有途经城市列表")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: List[DayPlan] = Field(..., description="每日行程")
    weather_info: List[WeatherInfo] = Field(default=[], description="天气信息")
    overall_suggestions: str = Field(..., description="总体建议")
    budget: Optional[Budget] = Field(default=None, description="预算信息")


# ============ 知识图谱数据模型 ============

class GraphNode(BaseModel):
    """图谱节点"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    category: int = Field(default=0, description="分类索引")
    symbolSize: int = Field(default=30, description="节点大小")
    itemStyle: Optional[dict] = Field(default=None, description="节点样式")
    value: Optional[str] = Field(default="", description="附加信息")


class GraphEdge(BaseModel):
    """图谱边"""
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: str = Field(default="", description="关系标签")


class GraphCategory(BaseModel):
    """图谱分类"""
    name: str = Field(..., description="分类名称")


class KnowledgeGraphData(BaseModel):
    """知识图谱数据"""
    nodes: List[GraphNode] = Field(default=[], description="节点列表")
    edges: List[GraphEdge] = Field(default=[], description="边列表")
    categories: List[GraphCategory] = Field(default=[], description="分类列表")


class TripPlanResponse(BaseModel):
    """旅行计划响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    plan_id: Optional[str] = Field(default=None, description="计划ID（与后端任务ID对齐）")
    data: Optional[TripPlan] = Field(default=None, description="旅行计划数据")
    graph_data: Optional[KnowledgeGraphData] = Field(default=None, description="知识图谱数据")


class POIInfo(BaseModel):
    """POI信息"""
    id: str = Field(..., description="POI ID")
    name: str = Field(..., description="名称")
    type: str = Field(..., description="类型")
    address: str = Field(..., description="地址")
    location: Location = Field(..., description="经纬度坐标")
    tel: Optional[str] = Field(default=None, description="电话")


class POISearchResponse(BaseModel):
    """POI搜索响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: List[POIInfo] = Field(default=[], description="POI列表")


class RouteInfo(BaseModel):
    """路线信息"""
    distance: float = Field(..., description="距离(米)")
    duration: int = Field(..., description="时间(秒)")
    route_type: str = Field(..., description="路线类型")
    description: str = Field(..., description="路线描述")


class RouteResponse(BaseModel):
    """路线规划响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[RouteInfo] = Field(default=None, description="路线信息")


class WeatherResponse(BaseModel):
    """天气查询响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: List[WeatherInfo] = Field(default=[], description="天气信息")


# ============ 错误响应 ============

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")


# ============ AI 行程问答模型 ============

class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str = Field(..., description="角色: user / assistant")
    content: str = Field(..., description="消息内容")


class TripChatRequest(BaseModel):
    """行程问答请求"""
    message: str = Field(..., description="用户提问内容")
    trip_plan: dict = Field(..., description="当前旅行计划(JSON对象)")
    history: Optional[List[ChatMessage]] = Field(default=[], description="历史对话记录")


class TripChatResponse(BaseModel):
    """行程问答响应"""
    success: bool = Field(default=True, description="是否成功")
    reply: str = Field(..., description="AI回复内容")
