// 类型定义

export interface CityStay {
  city: string
  days: number
}

export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total_inter_city_transport?: number
  total: number
}

export interface DayPlan {
  date: string
  day_index: number
  city?: string
  is_transfer_day?: boolean
  transfer_info?: string
  description: string
  transportation: string
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
}

export interface WeatherInfo {
  date: string
  city?: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TripPlan {
  city: string
  cities?: string[]
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
}

export interface TripFormData {
  city: string
  cities?: CityStay[]
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
  language?: string
  user_id?: string
  hotel_selection?: HotelSelection | null
  selected_attractions?: SelectedAttraction[] | null
  daily_plan?: DayPlanAssignment[] | null
}

// ============ 景点选择（AttractionPicker） ============

export interface AttractionOption {
  name: string
  name_zh: string
  name_en: string
  reason: string
  duration?: number | null
  reservation_required: boolean
  reservation_tips: string
  mention_count: number
  location?: Location | null
  address: string
  rating?: string | null
  region: string
}

export interface AttractionRegionGroup {
  region: string
  attractions: AttractionOption[]
}

export interface AttractionSearchResponse {
  success: boolean
  message: string
  city: string
  regions: AttractionRegionGroup[]
}

export interface SelectedAttraction {
  name: string
  name_zh?: string
  name_en?: string
  location?: Location | null
  duration?: number | null
  reason?: string
  reservation_required?: boolean
  reservation_tips?: string
  region?: string
}

export interface DayPlanAssignment {
  day: number
  attraction_names: string[]
}

// ============ 住宿定制（HotelPicker） ============

export interface HotelSelection {
  name: string
  address: string
  location?: Location | null
  type: string
  rating?: string
  estimated_cost: number
}

export interface HotelCandidate {
  name: string
  address: string
  location?: Location | null
  hotel_type: string
  rating?: number | null
  estimated_cost?: number | null
  distance_m?: number | null
  rating_available: boolean
  rating_score: number
  price_score: number
  total_score: number
}

export type HotelSortMode = 'rating' | 'price' | 'cost_perf'

export interface HotelCandidatesRequest {
  city: string
  keywords?: string
  location?: Location | null
  radius: number
  accommodation_type: string
  price_min?: number | null
  price_max?: number | null
  sort_mode: HotelSortMode
  limit?: number
}

export interface HotelCandidatesResponse {
  success: boolean
  message: string
  center?: Location | null
  center_name: string
  radius: number
  sort_mode: string
  total_found: number
  candidates: HotelCandidate[]
}

export interface TripPlanResponse {
  success: boolean
  message: string
  plan_id?: string
  data?: TripPlan
  graph_data?: KnowledgeGraphData
}

export interface TripHistoryItem {
  plan_id: string
  task_id: string
  city: string
  start_date: string
  end_date: string
  travel_days: number
  updated_at: string
  overall_suggestions?: string
}

export type TripTaskStatus = 'processing' | 'completed' | 'failed'

export type TripTaskStage =
  | 'submitted'
  | 'initializing'
  | 'attraction_search'
  | 'weather_search'
  | 'hotel_search'
  | 'planning'
  | 'graph_building'
  | 'completed'
  | 'failed'

export interface TripTaskEvent {
  task_id: string
  plan_id: string
  status: TripTaskStatus
  stage: TripTaskStage
  progress: number
  message: string
  error?: string
  result?: TripPlanResponse
}

export interface BackendRuntimeSettings {
  vite_amap_web_key: string
  vite_amap_web_js_key: string
  google_maps_api_key: string
  google_maps_proxy: string
  xhs_cookie: string
  openai_api_key: string
  openai_base_url: string
  openai_model: string
}

export interface RuntimeSettings {
  api_base_url: string
  vite_amap_web_key: string
  vite_amap_web_js_key: string
  google_maps_api_key: string
  google_maps_proxy: string
  xhs_cookie: string
  openai_api_key: string
  openai_base_url: string
  openai_model: string
}

// ============ 知识图谱类型 ============

export interface GraphNode {
  id: string
  name: string
  category: number
  symbolSize: number
  itemStyle?: { color: string }
  value?: string
}

export interface GraphEdge {
  source: string
  target: string
  label?: string
}

export interface GraphCategory {
  name: string
}

export interface KnowledgeGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  categories: GraphCategory[]
}

// ============ AI 行程问答类型 ============

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TripChatRequest {
  message: string
  trip_plan: object
  history: ChatMessage[]
}

export interface TripChatResponse {
  success: boolean
  reply: string
}
