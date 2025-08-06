// Base Types
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at?: string;
}

// User Types
export interface User extends BaseEntity {
  email: string;
  username?: string;
  full_name?: string;
  bio?: string;
  avatar_url?: string;
  role: UserRole;
  status: UserStatus;
  is_verified: boolean;
  is_active: boolean;
  subscription_tier: string;
  total_quotes_generated: number;
  total_voice_requests: number;
  last_login_at?: string;
  display_name: string;
  timezone: string;
  language: string;
}

export enum UserRole {
  USER = 'user',
  PREMIUM = 'premium',
  MODERATOR = 'moderator',
  ADMIN = 'admin',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  DELETED = 'deleted',
}

// Authentication Types
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterCredentials {
  email: string;
  username?: string;
  full_name?: string;
  password: string;
  confirm_password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Quote Types
export interface Quote extends BaseEntity {
  text: string;
  author?: string;
  context?: string;
  user_id: string;
  category_id?: string;
  source: QuoteSource;
  ai_model?: string;
  psychological_profile?: Record<string, any>;
  emotional_tone?: string;
  sentiment_score?: number;
  complexity_score?: number;
  quality_score?: number;
  popularity_score: number;
  view_count: number;
  like_count: number;
  share_count: number;
  favorite_count: number;
  is_approved: boolean;
  is_featured: boolean;
  is_public: boolean;
  status: QuoteStatus;
  tags?: string[];
  word_count: number;
  character_count: number;
  is_long_quote: boolean;
}

export enum QuoteSource {
  AI_GENERATED = 'ai_generated',
  TEXT_INPUT = 'text_input',
  VOICE_INPUT = 'voice_input',
  IMPORTED = 'imported',
}

export enum QuoteStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
}

export interface QuoteCategory extends BaseEntity {
  name: string;
  slug: string;
  description?: string;
  color?: string;
  icon?: string;
  parent_id?: string;
  sort_order: number;
  is_active: boolean;
}

export interface QuoteGeneration {
  prompt: string;
  category?: string;
  style?: string;
  length?: 'short' | 'medium' | 'long';
  tone?: string;
  author_style?: string;
  context?: string;
  ai_model?: string;
  temperature?: number;
  max_tokens?: number;
  include_psychology?: boolean;
}

// Voice Types
export interface VoiceRecording extends BaseEntity {
  user_id: string;
  filename: string;
  original_filename?: string;
  file_path: string;
  file_size: number;
  file_format: AudioFormat;
  mime_type: string;
  duration_seconds?: number;
  sample_rate?: number;
  bit_rate?: number;
  channels?: number;
  recorded_at?: string;
  device_info?: Record<string, any>;
  quality_score?: number;
  status: VoiceRecordingStatus;
  transcription?: string;
  transcription_confidence?: number;
  language_detected?: string;
  speaker_count?: number;
  emotional_analysis?: Record<string, any>;
  content_categories?: string[];
  keywords?: string[];
  sentiment_score?: number;
  ai_model_used?: string;
  processing_duration?: number;
  processing_cost?: number;
  is_public: boolean;
  retain_audio: boolean;
  auto_delete_at?: string;
  processed_at?: string;
  is_processed: boolean;
  has_transcription: boolean;
  file_size_mb: number;
  duration_formatted: string;
}

export enum AudioFormat {
  WAV = 'wav',
  MP3 = 'mp3',
  OGG = 'ogg',
  M4A = 'm4a',
  FLAC = 'flac',
  WEBM = 'webm',
}

export enum VoiceRecordingStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  FAILED = 'failed',
  DELETED = 'deleted',
}

export interface VoiceProcessingJob extends BaseEntity {
  user_id: string;
  recording_id: string;
  job_type: string;
  parameters?: Record<string, any>;
  status: VoiceProcessingStatus;
  priority: number;
  model_config?: Record<string, any>;
  progress_percent: number;
  current_step?: string;
  steps_total?: number;
  steps_completed: number;
  result_data?: Record<string, any>;
  output_files?: string[];
  error_message?: string;
  error_code?: string;
  retry_count: number;
  max_retries: number;
  started_at?: string;
  completed_at?: string;
  processing_time?: number;
  cpu_time?: number;
  memory_peak?: number;
  credits_used?: number;
  cost_usd?: number;
  worker_id?: string;
  worker_version?: string;
  is_completed: boolean;
  is_failed: boolean;
  can_retry: boolean;
}

export enum VoiceProcessingStatus {
  PENDING = 'pending',
  STARTED = 'started',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Analytics Types
export interface AnalyticsEvent extends BaseEntity {
  user_id?: string;
  session_id?: string;
  event_type: EventType;
  event_name: string;
  event_category?: string;
  properties?: Record<string, any>;
  value?: number;
  page_url?: string;
  page_title?: string;
  referrer?: string;
  user_agent?: string;
  ip_address?: string;
  device_type?: string;
  browser?: string;
  operating_system?: string;
  screen_resolution?: string;
  country?: string;
  region?: string;
  city?: string;
  timezone?: string;
  timestamp: string;
  server_timestamp: string;
}

export enum EventType {
  PAGE_VIEW = 'page_view',
  USER_REGISTER = 'user_register',
  USER_LOGIN = 'user_login',
  USER_LOGOUT = 'user_logout',
  QUOTE_GENERATED = 'quote_generated',
  QUOTE_LIKED = 'quote_liked',
  QUOTE_SHARED = 'quote_shared',
  QUOTE_FAVORITED = 'quote_favorited',
  VOICE_RECORDING_STARTED = 'voice_recording_started',
  VOICE_RECORDING_COMPLETED = 'voice_recording_completed',
  VOICE_PROCESSING_COMPLETED = 'voice_processing_completed',
  FEATURE_USED = 'feature_used',
  SESSION_STARTED = 'session_started',
  SESSION_ENDED = 'session_ended',
  AI_ERROR_OCCURRED = 'ai_error_occurred',
  SUBSCRIPTION_UPGRADED = 'subscription_upgraded',
}

export interface UserSession extends BaseEntity {
  user_id?: string;
  session_token: string;
  anonymous_id?: string;
  started_at: string;
  ended_at?: string;
  last_activity_at: string;
  duration_seconds?: number;
  landing_page?: string;
  exit_page?: string;
  referrer?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  user_agent?: string;
  ip_address?: string;
  device_type?: string;
  browser?: string;
  operating_system?: string;
  country?: string;
  region?: string;
  city?: string;
  timezone?: string;
  page_views: number;
  quotes_generated: number;
  voice_recordings: number;
  interactions: number;
  bounce: boolean;
  engaged: boolean;
  converted: boolean;
  is_active: boolean;
}

// UI Types
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface Modal {
  id: string;
  title: string;
  content: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closable?: boolean;
  onClose?: () => void;
}

export interface DropdownOption {
  label: string;
  value: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
}

// API Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface APIError {
  detail: string;
  error_code?: string;
  field_errors?: Record<string, string[]>;
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  primaryColor: string;
  accentColor: string;
  fontSize: 'sm' | 'md' | 'lg';
  animations: boolean;
}

// Settings Types
export interface UserSettings {
  theme: ThemeConfig;
  notifications: {
    email: boolean;
    push: boolean;
    quote_generation: boolean;
    voice_processing: boolean;
    marketing: boolean;
  };
  privacy: {
    profile_public: boolean;
    quotes_public: boolean;
    analytics_tracking: boolean;
  };
  preferences: {
    default_quote_style: string;
    default_ai_model: string;
    auto_save: boolean;
    voice_auto_process: boolean;
  };
}

// Service Quote Types (Window/Pressure Cleaning)
export interface ServiceQuote extends BaseEntity {
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  customer_address: string;
  suburb: string;
  service_type: ServiceType;
  property_type: PropertyType;
  square_meters: number;
  stories: number;
  difficulty_multiplier: number;
  frequency: ServiceFrequency;
  base_price: number;
  total_price: number;
  zone_multiplier: number;
  frequency_discount: number;
  special_requirements?: string;
  notes?: string;
  status: ServiceQuoteStatus;
  valid_until: string;
  ai_confidence?: number;
  voice_recording_id?: string;
  pricing_breakdown: PricingBreakdown;
  estimated_duration: number;
  contact_preference: ContactPreference;
  preferred_contact_time?: string;
  quote_source: QuoteSource;
}

export enum ServiceType {
  WINDOW_CLEANING = 'window_cleaning',
  PRESSURE_CLEANING = 'pressure_cleaning',
  BOTH = 'both'
}

export enum PropertyType {
  HOUSE = 'house',
  APARTMENT = 'apartment',
  COMMERCIAL = 'commercial',
  TOWNHOUSE = 'townhouse'
}

export enum ServiceFrequency {
  ONE_TIME = 'one_time',
  WEEKLY = 'weekly',
  FORTNIGHTLY = 'fortnightly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly'
}

export enum ServiceQuoteStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired'
}

export enum ContactPreference {
  EMAIL = 'email',
  PHONE = 'phone',
  SMS = 'sms'
}

export enum QuoteSource {
  MANUAL = 'manual',
  VOICE = 'voice',
  API = 'api'
}

export interface PricingBreakdown {
  base_rate: number;
  area_cost: number;
  story_multiplier: number;
  difficulty_adjustment: number;
  zone_adjustment: number;
  frequency_discount: number;
  total_before_discount: number;
  discount_amount: number;
  final_total: number;
}

export interface ServiceQuoteRequest {
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  customer_address: string;
  suburb: string;
  service_type: ServiceType;
  property_type: PropertyType;
  square_meters: number;
  stories: number;
  difficulty_multiplier?: number;
  frequency: ServiceFrequency;
  special_requirements?: string;
  notes?: string;
  contact_preference: ContactPreference;
  preferred_contact_time?: string;
}

export interface ServiceQuoteCalculation {
  service_type: ServiceType;
  property_type: PropertyType;
  square_meters: number;
  stories: number;
  suburb: string;
  frequency: ServiceFrequency;
  difficulty_multiplier?: number;
}

export interface SuburbInfo {
  name: string;
  zone: string;
  base_rate_multiplier: number;
}

// Voice to Service Quote
export interface VoiceServiceQuoteRequest {
  audio_file: File;
  additional_data?: Partial<ServiceQuoteRequest>;
}