// Type definitions for the transaction analysis application

export interface Transaction {
  transaction_id: number;
  user_id: number;
  user_name: string;
  user_username: string;
  user_mobile: number;
  reciever_id: number;
  reciever_name: string;
  reciever_mobile: number;
  amount: number;
  total_amount: number;
  currency: string;
  settleable_amount: number;
  minimum_amount: number;
  order_status: string;
  payment_status: string;
  refund_status: string;
  bill_type: string;
  pg_transaction_id: string;
  specific_step_transaction_id?: number;
  payment_vendor: string;
  utr_number: string;
  image?: any;
  remarks: string;
  reference_id: string;
  created_at: string;
  updated_at: string;
}

export interface SuspiciousThread {
  thread_id: string;
  description: string;
  participants: string[];
  risk_level: 'high' | 'medium' | 'low';
  evidence: string[];
  transactions_involved: string[];
  potential_violation: string;
  pattern_type?: string;
  confidence_score?: number;
  recommended_action?: string;
}

export interface PatternAnalysis {
  threads: SuspiciousThread[];
  risk_level: 'high' | 'medium' | 'low';
  summary: string;
  key_insights?: string[];
}

export interface OverallAssessment {
  total_threads: number;
  overall_risk_level: 'high' | 'medium' | 'low';
  executive_summary: string;
  pattern_summary: {
    [key: string]: {
      thread_count: number;
      risk_level: 'high' | 'medium' | 'low';
    };
  };
  top_threats: SuspiciousThread[];
}

export interface AnalysisResult {
  frequent_pairs?: PatternAnalysis;
  round_amounts?: PatternAnalysis;
  high_activity_periods?: PatternAnalysis;
  repeated_amounts?: PatternAnalysis;
  quick_successive?: PatternAnalysis;
  overall_assessment?: OverallAssessment;
}

export interface FrequentPair {
  sender_id: number;
  receiver_id: number;
  sender_name: string;
  receiver_name: string;
  transaction_count: number;
  total_amount: number;
  average_amount: number;
  amount_std: number;
  first_transaction: string;
  last_transaction: string;
  sample_transactions: Transaction[];
}

export interface RoundAmountTransaction {
  transaction_id: number;
  user_name: string;
  reciever_name: string;
  amount: number;
  created_at: string;
  remarks: string;
}

export interface HighActivityPeriod {
  time_period: string;
  transaction_count: number;
  unique_users: number;
  total_amount: number;
  sample_transactions: Transaction[];
}

export interface RepeatedAmount {
  amount: number;
  frequency: number;
  unique_senders: number;
  unique_receivers: number;
  sample_transactions: Transaction[];
}

export interface QuickTransaction {
  transaction_id: number;
  user_name: string;
  reciever_name: string;
  amount: number;
  time_diff: number;
  created_at: string;
}

export interface PatternData {
  frequent_pairs: FrequentPair[];
  round_amounts: RoundAmountTransaction[];
  high_activity_periods: HighActivityPeriod[];
  repeated_amounts: RepeatedAmount[];
  quick_successive: QuickTransaction[];
}

export interface SummaryStats {
  total_transactions: number;
  unique_users: number;
  unique_receivers: number;
  total_amount: number;
  average_amount: number;
  date_range: {
    start: string;
    end: string;
  };
  payment_statuses: { [key: string]: number };
  top_users_by_transaction_count: { [key: string]: number };
  top_amounts: { [key: string]: number };
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  timestamp: string;
  cached?: boolean;
  mock?: boolean;
  partial?: boolean;
  message?: string;
}
