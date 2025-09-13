"""
Data processing module for transaction analysis.
Handles loading, cleaning, and preparing transaction data for LLM analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionProcessor:
    """pattern analysis."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.processed_data = None
        
    def load_data(self) -> pd.DataFrame:
        """Load data from CSV or Excel"""
        try:
            if self.file_path.lower().endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            else:
                self.df = pd.read_excel(self.file_path)
            logger.info(f"Loaded {len(self.df)} transactions from {self.file_path}")
            return self.df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def clean_data(self) -> pd.DataFrame:
        """Clean and preprocess data."""
        if self.df is None:
            self.load_data()
        
        # Create a copy for processing
        df_clean = self.df.copy()
        
        # Convert datetime columns
        df_clean['created_at'] = pd.to_datetime(df_clean['created_at'])
        df_clean['updated_at'] = pd.to_datetime(df_clean['updated_at'])
        
        # Handle missing values
        df_clean['remarks'] = df_clean['remarks'].fillna('No remarks')
        df_clean['utr_number'] = df_clean['utr_number'].fillna('No UTR')
        
        # Create derived features
        df_clean['transaction_hour'] = df_clean['created_at'].dt.hour
        df_clean['transaction_day'] = df_clean['created_at'].dt.day_name()
        df_clean['processing_time'] = (df_clean['updated_at'] - df_clean['created_at']).dt.total_seconds()
        
        # Flag potential anomalies
        df_clean['is_large_amount'] = df_clean['amount'] > df_clean['amount'].quantile(0.95) # top 5
        df_clean['is_quick_processing'] = df_clean['processing_time'] < 60  # Less than 1 minute
        
        self.processed_data = df_clean
        logger.info("Data cleaning completed")
        return df_clean
    
    def identify_potential_patterns(self) -> Dict[str, Any]:
        """Identify potential patterns for LLM analysis."""
        if self.processed_data is None:
            self.clean_data()
        
        df = self.processed_data
        patterns = {}
        
        # Frequent user pairs (same sender-receiver combinations)
        user_pairs = df.groupby(['user_id', 'reciever_id']).agg({
            'transaction_id': 'count',
            'amount': ['sum', 'mean', 'std'],
            'created_at': ['min', 'max']
        }).round(2)
        
        frequent_pairs = user_pairs[user_pairs[('transaction_id', 'count')] >= 3]
        patterns['frequent_pairs'] = self._format_frequent_pairs(frequent_pairs, df)
        
        # Round number transactions (potentially suspicious)
        round_amounts = df[df['amount'] % 1000 == 0]
        patterns['round_amounts'] = self._format_round_amounts(round_amounts)
        
        # High-frequency trading periods
        df['hour_bucket'] = df['created_at'].dt.floor('h')
        hourly_counts = df.groupby('hour_bucket').size()
        high_activity_hours = hourly_counts[hourly_counts > hourly_counts.quantile(0.9)]
        patterns['high_activity_periods'] = self._format_high_activity(high_activity_hours, df)
        
        # Similar amount patterns
        amount_groups = df.groupby('amount').size()
        repeated_amounts = amount_groups[amount_groups >= 3]
        patterns['repeated_amounts'] = self._format_repeated_amounts(repeated_amounts, df)
        
        # Quick successive transactions
        df_sorted = df.sort_values(['user_id', 'created_at'])
        df_sorted['time_diff'] = df_sorted.groupby('user_id')['created_at'].diff().dt.total_seconds()
        quick_transactions = df_sorted[df_sorted['time_diff'] <= 300]  # Within 5 minutes
        patterns['quick_successive'] = self._format_quick_transactions(quick_transactions)
        
        logger.info(f"Identified {len(patterns)} pattern categories")
        return patterns
    
    def _format_frequent_pairs(self, frequent_pairs: pd.DataFrame, df: pd.DataFrame) -> List[Dict]:
        """Format frequent user pairs for analysis."""
        results = []
        for (user_id, receiver_id), data in frequent_pairs.iterrows():
            pair_transactions = df[(df['user_id'] == user_id) & (df['reciever_id'] == receiver_id)]
            
            results.append({
                'sender_id': user_id,
                'receiver_id': receiver_id,
                'sender_name': pair_transactions.iloc[0]['user_name'],
                'receiver_name': pair_transactions.iloc[0]['reciever_name'],
                'transaction_count': int(data[('transaction_id', 'count')]),
                'total_amount': float(data[('amount', 'sum')]),
                'average_amount': float(data[('amount', 'mean')]),
                'amount_std': float(data[('amount', 'std')]) if not pd.isna(data[('amount', 'std')]) else 0,
                'first_transaction': data[('created_at', 'min')].strftime('%Y-%m-%d %H:%M:%S'),
                'last_transaction': data[('created_at', 'max')].strftime('%Y-%m-%d %H:%M:%S'),
                'sample_transactions': [
                    {
                        'transaction_id': int(row['transaction_id']),
                        'amount': float(row['amount']),
                        'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                        'remarks': str(row['remarks'])
                    }
                    for _, row in pair_transactions[['transaction_id', 'amount', 'created_at', 'remarks']].head(3).iterrows()
                ]
            })
        
        return sorted(results, key=lambda x: x['transaction_count'], reverse=True)
    
    def _format_round_amounts(self, round_amounts: pd.DataFrame) -> List[Dict]:
        """Format round amount transactions."""
        results = []
        for _, row in round_amounts[['transaction_id', 'user_name', 'reciever_name', 'amount', 'created_at', 'remarks']].iterrows():
            results.append({
                'transaction_id': int(row['transaction_id']),
                'user_name': str(row['user_name']),
                'reciever_name': str(row['reciever_name']),
                'amount': float(row['amount']),
                'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'remarks': str(row['remarks'])
            })
        return results
    
    def _format_high_activity(self, high_activity_hours: pd.Series, df: pd.DataFrame) -> List[Dict]:
        """Format high activity periods."""
        results = []
        for hour, count in high_activity_hours.items():
            hour_transactions = df[df['hour_bucket'] == hour]
            results.append({
                'time_period': hour.strftime('%Y-%m-%d %H:%M:%S'),
                'transaction_count': int(count),
                'unique_users': hour_transactions['user_id'].nunique(),
                'total_amount': float(hour_transactions['amount'].sum()),
                'sample_transactions': [
                    {
                        'transaction_id': int(row['transaction_id']),
                        'user_name': str(row['user_name']),
                        'amount': float(row['amount'])
                    }
                    for _, row in hour_transactions[['transaction_id', 'user_name', 'amount']].head(5).iterrows()
                ]
            })
        
        return sorted(results, key=lambda x: x['transaction_count'], reverse=True)
    
    def _format_repeated_amounts(self, repeated_amounts: pd.Series, df: pd.DataFrame) -> List[Dict]:
        """Format repeated amount patterns."""
        results = []
        for amount, count in repeated_amounts.items():
            amount_transactions = df[df['amount'] == amount]
            results.append({
                'amount': float(amount),
                'frequency': int(count),
                'unique_senders': amount_transactions['user_id'].nunique(),
                'unique_receivers': amount_transactions['reciever_id'].nunique(),
                'sample_transactions': [
                    {
                        'transaction_id': int(row['transaction_id']),
                        'user_name': str(row['user_name']),
                        'reciever_name': str(row['reciever_name']),
                        'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    for _, row in amount_transactions[['transaction_id', 'user_name', 'reciever_name', 'created_at']].head(3).iterrows()
                ]
            })
        
        return sorted(results, key=lambda x: x['frequency'], reverse=True)
    
    def _format_quick_transactions(self, quick_transactions: pd.DataFrame) -> List[Dict]:
        """Format quick successive transactions."""
        results = []
        for _, row in quick_transactions[['transaction_id', 'user_name', 'reciever_name', 'amount', 'time_diff', 'created_at']].iterrows():
            results.append({
                'transaction_id': int(row['transaction_id']),
                'user_name': str(row['user_name']),
                'reciever_name': str(row['reciever_name']),
                'amount': float(row['amount']),
                'time_diff': float(row['time_diff']) if not pd.isna(row['time_diff']) else 0,
                'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            })
        return results
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dataset."""
        if self.processed_data is None:
            self.clean_data()
        
        df = self.processed_data
        
        return {
            'total_transactions': len(df),
            'unique_users': df['user_id'].nunique(),
            'unique_receivers': df['reciever_id'].nunique(),
            'total_amount': float(df['amount'].sum()),
            'average_amount': float(df['amount'].mean()),
            'date_range': {
                'start': df['created_at'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['created_at'].max().strftime('%Y-%m-%d %H:%M:%S')
            },
            'payment_statuses': df['payment_status'].value_counts().to_dict(),
            'top_users_by_transaction_count': df['user_name'].value_counts().head(5).to_dict(),
            'top_amounts': df['amount'].value_counts().head(10).to_dict()
        }
